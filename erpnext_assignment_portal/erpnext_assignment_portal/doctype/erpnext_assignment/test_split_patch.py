import frappe
from frappe.tests.utils import FrappeTestCase
from erpnext_assignment_portal.patches.v0_0_1.split_days_into_sections import (
	execute as split_execute,
	slice_markdown,
)


class TestSplitPatch(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_slice_markdown_by_heading(self):
		md = "## Company\nCreate a company.\n## Fiscal Year\nMake a FY."
		slices = slice_markdown(md, ["Company", "Fiscal Year"])
		self.assertIn("Create a company", slices["Company"])
		self.assertIn("Make a FY", slices["Fiscal Year"])

	def test_explode_creates_one_row_per_key(self):
		checks = {
			"ZZ Alpha Section": [{"title": "Co", "doctype": "Company", "name": "X",
				"checks": [{"heading": "a", "check_type": "match"}]}],
			"ZZ Beta Section": [{"title": "St", "doctype": "Warehouse", "name": "Y",
				"checks": [{"heading": "b", "check_type": "match"}]}],
		}
		legacy = frappe.get_doc({
			"doctype": "ERPNext Assignment",
			"section": "ZZ Legacy Day",
			"published": 1,
			"assignment_details": "## ZZ Alpha Section\nDo alpha.\n## ZZ Beta Section\nDo beta.",
			"checks": frappe.as_json(checks),
		}).insert(ignore_permissions=True)

		split_execute()

		self.assertTrue(frappe.db.exists("ERPNext Assignment", "zz-alpha-section"))
		self.assertTrue(frappe.db.exists("ERPNext Assignment", "zz-beta-section"))
		self.assertFalse(frappe.db.exists("ERPNext Assignment", legacy.name))
		alpha = frappe.get_doc("ERPNext Assignment", "zz-alpha-section")
		self.assertEqual(alpha.section, "ZZ Alpha Section")
		self.assertIn("Do alpha", alpha.assignment_details)
		# idempotent: re-run does not duplicate
		split_execute()
		self.assertEqual(frappe.db.count("ERPNext Assignment", {"section": "ZZ Alpha Section"}), 1)

	def test_total_checks_set_when_no_matching_heading(self):
		"""Exploded rows whose source markdown has no matching heading (empty slice)
		must still have total_checks set correctly — validate() is bypassed by the patch."""
		checks = {
			"ZZ Has Heading": [{"title": "H", "doctype": "Company", "name": "X",
				"checks": [{"heading": "c1", "check_type": "match"},
				           {"heading": "c2", "check_type": "match"}]}],
			"ZZ No Heading": [{"title": "N", "doctype": "Warehouse", "name": "Y",
				"checks": [{"heading": "c3", "check_type": "match"},
				           {"heading": "c4", "check_type": "match"}]}],
		}
		# Markdown only contains a heading for "ZZ Has Heading"; "ZZ No Heading" gets no slice.
		frappe.get_doc({
			"doctype": "ERPNext Assignment",
			"section": "ZZ Legacy Day Two",
			"published": 1,
			"assignment_details": "## ZZ Has Heading\nDo the thing.",
			"checks": frappe.as_json(checks),
		}).insert(ignore_permissions=True)

		split_execute()

		# Both rows must exist even though one has an empty details slice.
		self.assertTrue(frappe.db.exists("ERPNext Assignment", "zz-has-heading"))
		self.assertTrue(frappe.db.exists("ERPNext Assignment", "zz-no-heading"))

		has_heading = frappe.get_doc("ERPNext Assignment", "zz-has-heading")
		no_heading = frappe.get_doc("ERPNext Assignment", "zz-no-heading")

		# Each key carries 2 checks; total_checks must reflect that regardless of the
		# empty-slice path that bypassed validate().
		self.assertEqual(has_heading.total_checks, 2)
		self.assertEqual(no_heading.total_checks, 2)
		self.assertEqual(no_heading.assignment_details, "")

	def test_slice_markdown_normalization(self):
		"""Heading '## Fiscal-Year' (punctuation) matches section 'Fiscal Year' via normalization."""
		md = "## Fiscal-Year\nMake a FY.\n## Company\nCreate a company."
		slices = slice_markdown(md, ["Fiscal Year", "Company"])
		self.assertIn("Make a FY", slices["Fiscal Year"])
		self.assertIn("Create a company", slices["Company"])

	def test_slice_markdown_matches_singular_heading(self):
		"""Singular heading '## Customer' matches plural section 'Customers' via loose substring fallback."""
		md = "## Customer\nCreate two customers."
		slices = slice_markdown(md, ["Customers"])
		self.assertIn("Create two customers", slices["Customers"])

	def test_backfills_section_on_single_key_row(self):
		single = frappe.get_doc({
			"doctype": "ERPNext Assignment",
			"section": "ZZ Single",  # will be replaced by backfill to the checks key
			"checks": frappe.as_json({"ZZ Solo Section": [{"title": "T", "doctype": "Company",
				"name": "X", "checks": [{"heading": "a", "check_type": "match"}]}]}),
		}).insert(ignore_permissions=True)
		# Simulate a legacy single-key row whose section is unset.
		frappe.db.set_value("ERPNext Assignment", single.name, "section", None, update_modified=False)
		split_execute()
		self.assertEqual(frappe.db.get_value("ERPNext Assignment", single.name, "section"), "ZZ Solo Section")
