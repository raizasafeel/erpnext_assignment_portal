import frappe
from frappe.tests import IntegrationTestCase

from erpnext_assignment_portal.constants import ROLE, SECTION, SETTINGS


class TestDoctypes(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)

	def make_section(self, filters):
		return frappe.get_doc(
			{
				"doctype": SECTION,
				"slug": "probe-section",
				"title": "Probe",
				"checks": [{"title": "c", "target_doctype": "Warehouse", "filters": filters}],
			}
		)

	def test_check_id_is_assigned_and_stable(self):
		s = self.make_section([["name", "=", "x"]]).insert()
		check_id = s.checks[0].check_id
		self.assertTrue(check_id)
		s.checks[0].title = "renamed"
		s.save()
		self.assertEqual(s.checks[0].check_id, check_id)

	def test_filter_shape_is_validated(self):
		for bad in (
			'"x"',
			'[["name"]]',
			'[["name","regexp","x"]]',
			'[["name","is","maybe"]]',
			'[["name","in","x"]]',
		):
			with self.subTest(bad=bad):
				doc = self.make_section(bad)
				doc.slug = frappe.generate_hash(length=8)
				self.assertRaises(frappe.ValidationError, doc.insert)

	def test_slug_cannot_change(self):
		s = self.make_section([["name", "=", "x"]])
		s.slug = "probe-slug-lock"
		s.insert()
		s.slug = "other"
		try:
			s.save()
		except frappe.CannotChangeConstantError:
			pass
		self.assertEqual(frappe.db.get_value(SECTION, "probe-slug-lock", "slug"), "probe-slug-lock")
		self.assertFalse(frappe.db.exists(SECTION, "other"))

	def test_defaults_seeded(self):
		self.assertTrue(frappe.db.exists("Role", ROLE))
		self.assertIn("*.m.frappe.cloud", frappe.get_single(SETTINGS).host_patterns())
