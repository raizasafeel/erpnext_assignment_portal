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
		self.assertTrue(context.favicon)
		self.assertTrue(context.title)
