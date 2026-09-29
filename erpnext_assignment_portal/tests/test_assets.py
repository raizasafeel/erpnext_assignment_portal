import os

import frappe
from frappe.tests import IntegrationTestCase

APP = "erpnext_assignment_portal"


class TestAssets(IntegrationTestCase):
	def test_apps_screen_logo_exists(self):
		apps = frappe.get_hooks("add_to_apps_screen", app_name=APP)
		self.assertTrue(apps)
		for app in apps:
			with self.subTest(logo=app["logo"]):
				relative = app["logo"].removeprefix(f"/assets/{APP}/")
				self.assertTrue(os.path.isfile(frappe.get_app_path(APP, "public", relative)))
