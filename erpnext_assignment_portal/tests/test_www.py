import frappe
from frappe.tests import IntegrationTestCase

from erpnext_assignment_portal.www import assignment_portal


class TestPortalPage(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.set_user, frappe.session.user)
		self.addCleanup(frappe.local.flags.pop, "redirect_location", None)

	# Regression: a guest got the SPA shell instead of the login page (commit 4945a01).
	def test_guest_is_redirected_to_login(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.Redirect):
			assignment_portal.get_context(frappe._dict())
		self.assertEqual(
			frappe.local.flags.redirect_location, "/login?redirect-to=/assignments-portal/erpnext"
		)

	def test_logged_in_user_gets_boot_and_page_meta(self):
		frappe.set_user("Administrator")
		context = assignment_portal.get_context(frappe._dict())
		self.assertEqual(context.boot.site_name, frappe.local.site)
		self.assertEqual(context.favicon, "/assets/erpnext_assignment_portal/images/logo.svg")
		self.assertTrue(context.title)

	def test_boot_names_the_course_for_the_not_enrolled_page(self):
		self.addCleanup(frappe.db.rollback)
		course = frappe.db.get_value("LMS Course", {}, ["name", "title"], as_dict=True)
		if not course:
			self.skipTest("no LMS Course on this site")
		frappe.db.set_single_value("Grader Settings", "course", course.name)
		frappe.set_user("Administrator")
		boot = assignment_portal.get_context(frappe._dict()).boot
		self.assertEqual(boot.course, {"name": course.name, "title": course.title})
