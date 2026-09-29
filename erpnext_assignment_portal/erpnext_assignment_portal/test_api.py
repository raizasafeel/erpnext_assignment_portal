import frappe
from frappe.tests.utils import FrappeTestCase
from erpnext_assignment_portal.erpnext_assignment_portal import api


class TestGraderAPI(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_get_assignments_returns_section_fields(self):
		frappe.get_doc({"doctype": "ERPNext Assignment", "section": "ZZ Customers",
			"section_order": 2, "blurb": "Two customers", "published": 1,
			"assignment_details": "do it",
			"checks": frappe.as_json({"ZZ Customers": [{"title": "C", "doctype": "Customer",
				"name": "X", "checks": [{"heading": "a", "check_type": "match"}]}]})}).insert(ignore_permissions=True)
		rows = api.get_assignments()
		self.assertTrue(any(r["section"] == "ZZ Customers" and r["section_order"] == 2 for r in rows))
		self.assertIn("blurb", rows[0])
		self.assertNotIn("day", rows[0])

	def test_split_results_per_section(self):
		from erpnext_assignment_portal.erpnext_assignment_portal.api import _submissions_from_results
		results = [
			{"label": "a", "passed": True, "section": "Company", "title": "Co", "expected": "", "actual": ""},
			{"label": "b", "passed": False, "section": "Company", "title": "Co", "expected": "", "actual": ""},
			{"label": "c", "passed": True, "section": "Stock", "title": "St", "expected": "", "actual": ""},
		]
		grouped = _submissions_from_results(results)
		self.assertEqual(grouped["Company"]["passed"], 1)
		self.assertEqual(grouped["Company"]["total"], 2)
		self.assertEqual(grouped["Company"]["status"], "Failed")
		self.assertEqual(grouped["Stock"]["status"], "Passed")
