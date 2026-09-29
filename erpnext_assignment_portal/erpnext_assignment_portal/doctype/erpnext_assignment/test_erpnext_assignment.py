# Copyright (c) 2026, Raiza and contributors
import frappe
from frappe.tests.utils import FrappeTestCase


class TestERPNextAssignment(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def _make(self, section, checks=None, **kw):
		doc = frappe.get_doc(
			{
				"doctype": "ERPNext Assignment",
				"section": section,
				"checks": frappe.as_json(checks or {}),
				**kw,
			}
		).insert(ignore_permissions=True)
		return doc

	# ZZ-prefixed section names keep these fixtures from colliding with the real
	# migrated rows (company-setup, customers, …), which would otherwise force a
	# numeric suffix and break the slug assertions.
	def test_autoname_slugs_section(self):
		doc = self._make("ZZ Company Setup")
		self.assertEqual(doc.name, "zz-company-setup")

	def test_autoname_suffixes_on_collision(self):
		a = self._make("ZZ Company Setup")
		b = self._make("ZZ Company Setup")
		self.assertEqual(a.name, "zz-company-setup")
		self.assertEqual(b.name, "zz-company-setup-2")

	def test_total_checks_counted(self):
		checks = {"ZZ Company": [{"title": "Co", "doctype": "Company", "name": "X",
			"checks": [{"heading": "a", "check_type": "match"},
			           {"heading": "b", "check_type": "match"}]}]}
		doc = self._make("ZZ Company", checks=checks)
		self.assertEqual(doc.total_checks, 2)

	def test_published_requires_checks(self):
		with self.assertRaises(frappe.ValidationError):
			self._make("ZZ Empty", published=1, assignment_details="hi")
