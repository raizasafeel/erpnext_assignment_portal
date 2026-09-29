from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from erpnext_assignment_portal import linking
from erpnext_assignment_portal.constants import STUDENT_SITE
from erpnext_assignment_portal.remote import RemoteError
from erpnext_assignment_portal.tests.utils import ensure_settings, make_student

SITE = "https://rza.m.frappe.cloud"


@patch("erpnext_assignment_portal.linking.post_signed", return_value={"ok": True})
class TestLinking(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		ensure_settings()
		self.a = make_student("grader-a@example.com")
		self.b = make_student("grader-b@example.com")

	def test_links_and_sends_student_email(self, post):
		name = linking.link_site(self.a, SITE + "/")
		row = frappe.db.get_value(STUDENT_SITE, name, ["student", "site", "status"], as_dict=True)
		self.assertEqual((row.student, row.site, row.status), (self.a, SITE, "Active"))
		self.assertEqual(post.call_args.args[2], {"email": self.a})

	def test_owner_check_false_or_unreachable_refuses(self, post):
		for effect in (
			{"return_value": {"ok": False}},
			{"side_effect": RemoteError("unreachable")},
			{"return_value": {"ok": "yes"}},
		):
			with (
				self.subTest(effect=effect),
				patch("erpnext_assignment_portal.linking.post_signed", **effect),
			):
				self.assertRaises(frappe.ValidationError, linking.link_site, self.a, SITE)
		self.assertFalse(frappe.db.exists(STUDENT_SITE, {"student": self.a}))

	def test_relink_updates_same_row(self, post):
		first = linking.link_site(self.a, SITE)
		second = linking.link_site(self.a, "https://other.m.frappe.cloud")
		self.assertEqual(first, second)
		self.assertEqual(frappe.db.get_value(STUDENT_SITE, first, "site"), "https://other.m.frappe.cloud")

	def test_revoked_student_relinks_on_existing_row(self, post):
		first = linking.link_site(self.a, SITE)
		frappe.db.set_value(STUDENT_SITE, first, {"status": "Revoked", "expires_on": "2020-01-01 00:00:00"})
		second = linking.link_site(self.a, SITE)
		self.assertEqual(first, second)
		self.assertEqual(frappe.db.count(STUDENT_SITE, {"student": self.a}), 1)
		self.assertEqual(frappe.db.get_value(STUDENT_SITE, second, "status"), "Active")

	def test_second_student_cannot_link_same_site(self, post):
		linking.link_site(self.a, SITE)
		with self.assertRaises(frappe.ValidationError) as ctx:
			linking.link_site(self.b, SITE)
		self.assertIn("already linked", str(ctx.exception))

	def test_unique_index_decides_a_race(self, post):
		def other_student_links_first(site, method, payload):
			# db_insert skips every controller check, as a concurrent request's commit would.
			frappe.get_doc(
				{"doctype": STUDENT_SITE, "student": self.a, "site": SITE, "status": "Active"}
			).db_insert()
			return {"ok": True}

		post.side_effect = other_student_links_first
		with self.assertRaises(frappe.ValidationError) as ctx:
			linking.link_site(self.b, SITE)
		self.assertIn("already linked", str(ctx.exception))
		self.assertNotIsInstance(ctx.exception, frappe.UniqueValidationError)
		self.assertEqual(frappe.db.count(STUDENT_SITE, {"site": SITE}), 1)

	def test_not_enrolled(self, post):
		c = make_student("grader-c@example.com", enrolled=False)
		self.assertRaises(frappe.PermissionError, linking.link_site, c, SITE)
		post.assert_not_called()
