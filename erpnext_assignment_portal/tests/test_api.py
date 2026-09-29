from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

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

	def fake_request(self) -> None:
		# rate_limit only counts inside a request; a fresh IP keeps the redis counter clean between runs.
		env = EnvironBuilder(method="POST", path="/api/method/x").get_environ()
		for attr, value in (("request", Request(env)), ("request_ip", frappe.generate_hash(length=12))):
			p = patch.object(frappe.local, attr, value, create=True)
			p.start()
			self.addCleanup(p.stop)

	@patch("erpnext_assignment_portal.api.linking.link_site", return_value="x")
	def test_link_site_rate_limited(self, link):
		frappe.set_user(self.a)
		self.fake_request()
		for _ in range(10):
			api.link_site("https://a.m.frappe.cloud")
		self.assertRaises(frappe.RateLimitExceededError, api.link_site, "https://a.m.frappe.cloud")
		self.assertEqual(link.call_count, 10)

	@patch("erpnext_assignment_portal.api.runs.start_run", return_value="r")
	def test_start_run_rate_limited_by_setting(self, start):
		frappe.db.set_single_value(SETTINGS, "run_rate_limit_per_hour", 2)
		frappe.set_user(self.a)
		self.fake_request()
		api.start_run()
		api.start_run()
		self.assertRaises(frappe.RateLimitExceededError, api.start_run)
		self.assertEqual(start.call_count, 2)

	def tearDown(self):
		frappe.set_user("Administrator")
