import frappe
from frappe.tests import IntegrationTestCase

from erpnext_assignment_portal.hosts import canonical_site

P = ["*.m.frappe.cloud"]


class TestHosts(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)

	def test_canonical_site_variants(self):
		for url in (
			"https://Rza.m.frappe.cloud",
			"https://rza.m.frappe.cloud/",
			"https://rza.m.frappe.cloud:443",
			" https://rza.m.frappe.cloud. ",
			"https://rza.m.frappe.cloud/#",
		):
			with self.subTest(url=url):
				self.assertEqual(canonical_site(url, P), "https://rza.m.frappe.cloud")

	def test_refused(self):
		for url in (
			"http://rza.m.frappe.cloud",
			"https://rza.m.frappe.cloud:8443",
			"https://rza.m.frappe.cloud/app",
			"https://u:p@rza.m.frappe.cloud",
			"https://rza.m.frappe.cloud?x=1",
			"https://evil.com",
			"https://m.frappe.cloud.evil.com",
			"rza.m.frappe.cloud",
			"",
			"https://[::1",
			"https://rza.m.frappe.cloud:99999",
		):
			with self.subTest(url=url):
				self.assertRaises(frappe.ValidationError, canonical_site, url, P)
