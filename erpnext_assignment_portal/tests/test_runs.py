from datetime import timedelta
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from erpnext_assignment_portal import runs
from erpnext_assignment_portal.constants import RUN, SECTION, STUDENT_SITE
from erpnext_assignment_portal.remote import RemoteError
from erpnext_assignment_portal.tests.utils import ensure_settings, make_student


class TestRuns(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		ensure_settings()
		frappe.db.delete(SECTION)
		self.section = frappe.get_doc(
			{
				"doctype": SECTION,
				"slug": "wh",
				"title": "Warehouses",
				"published": 1,
				"checks": [
					{
						"title": "Mumbai",
						"target_doctype": "Warehouse",
						"filters": '[["name","like","%Mumbai%"]]',
					},
					{
						"title": "Two+",
						"target_doctype": "Warehouse",
						"filters": "[]",
						"expected_min": 2,
						"expected_max": 5,
					},
				],
			}
		).insert()
		self.ids = [c.check_id for c in self.section.checks]
		self.user = make_student("grader-run@example.com")
		frappe.get_doc(
			{"doctype": STUDENT_SITE, "student": self.user, "site": "https://run.m.frappe.cloud"}
		).insert()
		self.enqueue = patch("erpnext_assignment_portal.runs.frappe.enqueue").start()
		self.addCleanup(patch.stopall)

	def test_start_run_dedupes(self):
		first = runs.start_run(self.user)
		self.assertEqual(runs.start_run(self.user), first)
		self.enqueue.assert_called_once()
		self.assertEqual(self.enqueue.call_args.kwargs["job_id"], f"grader-run::{first}")

	def test_stale_run_is_replaced(self):
		first = runs.start_run(self.user)
		frappe.db.set_value(RUN, first, "creation", now_datetime() - timedelta(minutes=11))
		second = runs.start_run(self.user)
		self.assertNotEqual(first, second)
		self.assertEqual(frappe.db.get_value(RUN, first, ["status", "error_code"]), ("Error", "internal"))

	def test_revoked_or_expired_refused(self):
		for values in ({"status": "Revoked"}, {"expires_on": now_datetime() - timedelta(days=1)}):
			with self.subTest(values=values):
				frappe.db.set_value(
					STUDENT_SITE, {"student": self.user}, {"status": "Active", "expires_on": None} | values
				)
				self.assertRaises(frappe.ValidationError, runs.start_run, self.user)

	def test_evaluate(self):
		sent = runs.published_checks()
		rows = runs.evaluate(
			sent, [{"check_id": self.ids[0], "found_count": 1}, {"check_id": self.ids[1], "found_count": 9}]
		)
		self.assertEqual([r["passed"] for r in rows], [1, 0])
		rows = runs.evaluate(
			sent,
			[{"check_id": self.ids[0], "error": "not_allowed"}, {"check_id": self.ids[1], "found_count": 3}],
		)
		self.assertEqual([(r["passed"], r["check_error"]) for r in rows], [(0, "not_allowed"), (1, None)])

	def test_evaluate_rejects_bad_results(self):
		sent = runs.published_checks()
		good = {"check_id": self.ids[1], "found_count": 1}
		for results in (
			None,
			[good],
			[good, good],
			[good, {"check_id": "zzz", "found_count": 1}],
			[good, {"check_id": self.ids[0], "found_count": True}],
			[good, {"check_id": self.ids[0], "found_count": -1}],
			[good, {"check_id": self.ids[0], "error": "boom"}],
		):
			with self.subTest(results=results):
				self.assertRaises(RemoteError, runs.evaluate, sent, results)

	def test_execute_run_done(self):
		name = runs.start_run(self.user)
		reply = {"results": [{"check_id": i, "found_count": 2} for i in self.ids]}
		with (
			patch("erpnext_assignment_portal.runs.post_signed", return_value=reply),
			patch("erpnext_assignment_portal.runs.frappe.publish_realtime") as rt,
		):
			runs.execute_run(name)
		run = frappe.get_doc(RUN, name)
		self.assertEqual((run.status, run.passed, run.total), ("Done", 2, 2))
		rt.assert_called_with(
			"grader_run", {"run": name, "status": "Done"}, user=self.user, after_commit=True
		)

	def test_execute_run_error(self):
		name = runs.start_run(self.user)
		with (
			patch("erpnext_assignment_portal.runs.post_signed", side_effect=RemoteError("rejected")),
			patch("erpnext_assignment_portal.runs.frappe.publish_realtime"),
		):
			runs.execute_run(name)
		self.assertEqual(frappe.db.get_value(RUN, name, ["status", "error_code"]), ("Error", "rejected"))

	def test_evaluates_against_sent_snapshot(self):
		name = runs.start_run(self.user)

		def edit_then_reply(site, method, payload):
			self.section.checks[1].expected_min = 100
			self.section.save()
			return {"results": [{"check_id": i, "found_count": 2} for i in self.ids]}

		with (
			patch("erpnext_assignment_portal.runs.post_signed", side_effect=edit_then_reply),
			patch("erpnext_assignment_portal.runs.frappe.publish_realtime"),
		):
			runs.execute_run(name)
		self.assertEqual(frappe.db.get_value(RUN, name, "passed"), 2)
