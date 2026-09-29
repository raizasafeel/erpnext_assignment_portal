import frappe
from frappe.tests.utils import FrappeTestCase
from erpnext_assignment_portal.patches.v0_0_1.rename_submission_day_to_section import execute as rename_execute
from erpnext_assignment_portal.patches.v0_0_1.split_submissions_by_section import execute as split_execute


def _result(section, passed):
	return {"label": "chk", "passed": passed, "section": section, "title": section}


class TestSplitSubmissions(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def setUp(self):
		# Per-section ERPNext Assignment rows the split relinks to. Their autonames
		# (scrub then "_"->"-") are the link targets the split patch must resolve.
		for sec in ("ZZ Alpha Section", "ZZ Beta Section"):
			if not frappe.db.exists("ERPNext Assignment", {"section": sec}):
				frappe.get_doc({
					"doctype": "ERPNext Assignment",
					"section": sec,
					"checks": frappe.as_json({sec: [{"title": "T", "doctype": "Company",
						"name": "X", "checks": [{"heading": "a", "check_type": "match"}, {"heading": "b", "check_type": "match"}]}]}),
				}).insert(ignore_permissions=True)
		# Student Site (autoname field:student -> a User docname).
		if not frappe.db.exists("ERPNext Assignment Student Site", "Administrator"):
			frappe.get_doc({
				"doctype": "ERPNext Assignment Student Site",
				"student": "Administrator",
				"site": "http://zz.localhost:8000",
			}).insert(ignore_permissions=True)

	def test_split_multi_section_submission(self):
		# Legacy row whose results span two sections: Alpha (2 passed of 2), Beta (1 of 2).
		results = [
			_result("ZZ Alpha Section", True),
			_result("ZZ Alpha Section", True),
			_result("ZZ Beta Section", True),
			_result("ZZ Beta Section", False),
		]
		legacy = frappe.get_doc({
			"doctype": "ERPNext Assignment Submission",
			"site": "Administrator",
			"section": "zz-alpha-section",  # arbitrary existing link; results drive the split
			"submission_time": "2026-04-27 00:00:00",
			"total_checks": 4,
			"passed_checks": 3,
			"percent": 75,
			"status": "Failed",
			"results": frappe.as_json(results),
		}).insert(ignore_permissions=True)

		split_execute()

		# Original multi-section row is gone.
		self.assertFalse(frappe.db.exists("ERPNext Assignment Submission", legacy.name))

		alpha = frappe.get_all("ERPNext Assignment Submission",
			filters={"section": "zz-alpha-section"}, fields=["name", "total_checks", "passed_checks", "status"])
		beta = frappe.get_all("ERPNext Assignment Submission",
			filters={"section": "zz-beta-section"}, fields=["name", "total_checks", "passed_checks", "status"])

		self.assertEqual(len(alpha), 1)
		self.assertEqual(len(beta), 1)
		self.assertEqual(alpha[0].total_checks, 2)
		self.assertEqual(alpha[0].passed_checks, 2)
		self.assertEqual(alpha[0].status, "Passed")
		self.assertEqual(beta[0].total_checks, 2)
		self.assertEqual(beta[0].passed_checks, 1)
		self.assertEqual(beta[0].status, "Failed")

		# Idempotent: re-run leaves the now single-section rows untouched.
		split_execute()
		self.assertEqual(
			frappe.db.count("ERPNext Assignment Submission", {"section": "zz-alpha-section"}), 1)
		self.assertEqual(
			frappe.db.count("ERPNext Assignment Submission", {"section": "zz-beta-section"}), 1)

	def test_single_section_row_left_untouched(self):  # N+1 per-section lookups are intentional for a one-time migration
		results = [_result("ZZ Alpha Section", True), _result("ZZ Alpha Section", False)]
		single = frappe.get_doc({
			"doctype": "ERPNext Assignment Submission",
			"site": "Administrator",
			"section": "zz-alpha-section",
			"submission_time": "2026-04-27 00:00:00",
			"total_checks": 2,
			"passed_checks": 1,
			"percent": 50,
			"status": "Failed",
			"results": frappe.as_json(results),
		}).insert(ignore_permissions=True)

		split_execute()

		# Single-section row is left in place (this is what makes re-runs no-ops).
		self.assertTrue(frappe.db.exists("ERPNext Assignment Submission", single.name))


class TestRenameSubmissionDayToSection(FrappeTestCase):
	"""Tests for the rename_submission_day_to_section patch."""

	def test_fresh_install_no_day_column_is_noop(self):
		# Fresh-install / already-migrated path: the table has no `day` column, so
		# execute() must return without raising. The SQL-copy branch (existing-site
		# upgrade with a legacy `day` column) is verified by `bench migrate`, not
		# unit-tested here, because adding/dropping a `day` column requires DDL that
		# MariaDB cannot roll back and would pollute the test DB.
		rename_execute()  # must not raise
