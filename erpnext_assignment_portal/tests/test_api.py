from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from erpnext_assignment_portal import api
from erpnext_assignment_portal.constants import RUN, SECTION, SETTINGS, STUDENT_SITE
from erpnext_assignment_portal.tests.utils import ensure_settings, make_student


class TestApi(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		ensure_settings()
		self.a = make_student("grader-api-a@example.com")
		self.b = make_student("grader-api-b@example.com")
		self.outsider = make_student("grader-api-x@example.com", enrolled=False)
		frappe.db.delete(SECTION)
		frappe.get_doc(
			{
				"doctype": SECTION,
				"slug": "s",
				"title": "S",
				"published": 1,
				"checks": [
					{
						"title": "c",
						"target_doctype": "Warehouse",
						"filters": '[["name","=","Secret"]]',
						"expected_min": 3,
					}
				],
			}
		).insert()
		site = frappe.get_doc(
			{"doctype": STUDENT_SITE, "student": self.b, "site": "https://b.m.frappe.cloud"}
		).insert()
		self.b_run = (
			frappe.get_doc({"doctype": RUN, "student": self.b, "student_site": site.name, "status": "Done"})
			.insert()
			.name
		)

	def test_sections_hide_answer_key(self):
		frappe.set_user(self.a)
		check = api.get_sections()[0]["checks"][0]
		self.assertEqual(set(check), {"check_id", "title"})

	def test_outsider_blocked_everywhere(self):
		frappe.set_user(self.outsider)
		for fn in (
			api.get_context,
			api.get_sections,
			api.start_run,
			lambda: api.get_run(self.b_run),
			lambda: api.link_site("https://x.m.frappe.cloud"),
		):
			with self.subTest(fn=fn):
				self.assertRaises(frappe.PermissionError, fn)

	def test_context_reports_revoked_site(self):
		frappe.set_user(self.b)
		self.assertFalse(api.get_context()["site"]["revoked"])
		frappe.db.set_value(STUDENT_SITE, {"student": self.b}, "status", "Revoked")
		site = api.get_context()["site"]
		self.assertTrue(site["revoked"])
		self.assertEqual(set(site), {"site", "status", "expires_on", "expired", "revoked"})

	def test_cannot_read_other_students_run(self):
		frappe.set_user(self.a)
		self.assertRaises(frappe.PermissionError, api.get_run, self.b_run)

	def test_certified_student_keeps_access(self):
		frappe.set_user("Administrator")
		frappe.get_doc(
			{
				"doctype": "LMS Certificate",
				"member": self.a,
				"course": frappe.db.get_single_value(SETTINGS, "course"),
				"issue_date": frappe.utils.today(),
			}
		).insert(ignore_permissions=True, ignore_mandatory=True)
		frappe.set_user(self.a)
		self.assertTrue(api.get_sections())

	def clear_link_counter(self, user):
		cache = frappe.cache() if callable(frappe.cache) else frappe.cache
		cache.delete(cache.make_key(f"grader-link-site:{user}"))

	@patch("erpnext_assignment_portal.api.linking.link_site", return_value="x")
	def test_link_site_limited_per_user(self, link):
		self.clear_link_counter(self.a)
		self.clear_link_counter(self.b)
		self.addCleanup(self.clear_link_counter, self.a)
		self.addCleanup(self.clear_link_counter, self.b)
		frappe.set_user(self.a)
		for _ in range(10):
			api.link_site("https://a.m.frappe.cloud")
		self.assertRaises(frappe.RateLimitExceededError, api.link_site, "https://a.m.frappe.cloud")
		self.assertEqual(link.call_count, 10)
		frappe.set_user(self.b)
		api.link_site("https://b.m.frappe.cloud")
		self.assertEqual(link.call_count, 11)

	@patch("erpnext_assignment_portal.api.linking.link_site", return_value="x")
	def test_outsider_does_not_spend_link_budget(self, link):
		self.clear_link_counter(self.outsider)
		self.addCleanup(self.clear_link_counter, self.outsider)
		frappe.set_user(self.outsider)
		for _ in range(12):
			self.assertRaises(frappe.PermissionError, api.link_site, "https://x.m.frappe.cloud")
		cache = frappe.cache() if callable(frappe.cache) else frappe.cache
		self.assertFalse(cache.get(cache.make_key(f"grader-link-site:{self.outsider}")))

	def link_student(self, user):
		return frappe.get_doc(
			{
				"doctype": STUDENT_SITE,
				"student": user,
				"site": f"https://{frappe.generate_hash(length=8)}.m.frappe.cloud",
			}
		).insert()

	def finish_runs(self, user):
		frappe.db.set_value(RUN, {"student": user}, "status", "Done")

	def test_start_run_limited_per_student(self):
		frappe.db.set_single_value(SETTINGS, "run_rate_limit_per_hour", 2)
		self.link_student(self.a)
		with patch("erpnext_assignment_portal.runs.frappe.enqueue"):
			frappe.set_user(self.a)
			for _ in range(2):
				api.start_run()
				self.finish_runs(self.a)
			self.assertRaises(frappe.RateLimitExceededError, api.start_run)
			self.assertEqual(frappe.db.count(RUN, {"student": self.a}), 2)
			frappe.set_user("Administrator")
			self.link_student("Administrator") if False else None
			frappe.set_user(self.b)
			frappe.db.delete(RUN, {"student": self.b})
			api.start_run()

	def test_deduped_active_run_does_not_count(self):
		frappe.db.set_single_value(SETTINGS, "run_rate_limit_per_hour", 1)
		self.link_student(self.a)
		with patch("erpnext_assignment_portal.runs.frappe.enqueue"):
			frappe.set_user(self.a)
			first = api.start_run()["run"]
			self.assertEqual(api.start_run()["run"], first)
			self.assertEqual(api.start_run()["run"], first)

	def test_outsider_does_not_spend_run_budget(self):
		frappe.set_user(self.outsider)
		self.assertRaises(frappe.PermissionError, api.start_run)
		self.assertEqual(frappe.db.count(RUN, {"student": self.outsider}), 0)

	def tearDown(self):
		frappe.set_user("Administrator")
