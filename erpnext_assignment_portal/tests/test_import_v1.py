import json
import os
import tempfile
from contextlib import redirect_stdout
from io import StringIO

import frappe
from frappe.tests import IntegrationTestCase

from erpnext_assignment_portal.import_v1 import convert_entry, run

BOM = {
	"doctype": "BOM",
	"title": "Bill of Materials",
	"name": "",
	"filter": [["docstatus", "=", 1], ["is_active", "=", 1]],
}


class TestImportV1(IntegrationTestCase):
	def test_match(self):
		e = BOM | {
			"checks": [
				{
					"check_type": "match",
					"heading": "BOM submitted",
					"fields_to_match": [{"currency": ["INR", "USD"]}],
				}
			]
		}
		[c] = convert_entry(e)
		self.assertEqual(
			c["filters"], [["docstatus", "=", 1], ["is_active", "=", 1], ["currency", "in", ["INR", "USD"]]]
		)
		self.assertEqual((c["title"], c["target_doctype"], c["expected_min"]), ("BOM submitted", "BOM", 1))

	def test_field_exists_with_name(self):
		e = {
			"doctype": "Company",
			"name": "Greenfield",
			"title": "Company",
			"checks": [
				{
					"check_type": "field_exists",
					"heading": "defaults",
					"fields_to_match": ["country", "cost_center"],
				}
			],
		}
		[c] = convert_entry(e)
		self.assertEqual(
			c["filters"],
			[["name", "=", "Greenfield"], ["country", "is", "set"], ["cost_center", "is", "set"]],
		)

	def test_exists_with_filter(self):
		e = {
			"doctype": "Account",
			"name": "",
			"title": "Bank",
			"checks": [
				{
					"check_type": "exists_with_filter",
					"heading": "Bank exists",
					"filter": [["name", "like", "%Bank Account%"]],
				}
			],
		}
		self.assertEqual(convert_entry(e)[0]["filters"], [["name", "like", "%Bank Account%"]])

	def test_child_has_row_splits_per_match(self):
		e = BOM | {
			"checks": [
				{
					"check_type": "child_has_row",
					"heading": "rows",
					"table": "items",
					"match": [{"item_code": "Steel"}, {"qty": 2}, {}],
				}
			]
		}
		got = [c["filters"][-1] for c in convert_entry(e)]
		self.assertEqual(
			got, [["items.item_code", "like", "%Steel%"], ["items.qty", "=", 2], ["items.name", "is", "set"]]
		)

	def test_name_list(self):
		e = {
			"doctype": "Item",
			"name": ["A", "B"],
			"title": "I",
			"checks": [{"check_type": "exists_with_filter", "heading": "h", "filter": []}],
		}
		self.assertEqual(convert_entry(e)[0]["filters"], [])
		e["checks"][0]["check_type"] = "match"
		e["checks"][0]["fields_to_match"] = []
		self.assertEqual(convert_entry(e)[0]["filters"], [["name", "in", ["A", "B"]]])

	def test_unknown_type(self):
		self.assertRaises(ValueError, convert_entry, {"doctype": "X", "checks": [{"check_type": "weird"}]})

	def test_normalises_v1_filter_shapes(self):
		price = {
			"doctype": "Item Price",
			"name": "",
			"title": "Price",
			"filter": {"item_code": "KB-WL", "price_list": "Standard Selling", "selling": 1},
			"checks": [
				{"check_type": "field_exists", "heading": "rate", "fields_to_match": ["price_list_rate"]}
			],
		}
		self.assertEqual(
			convert_entry(price)[0]["filters"],
			[
				["item_code", "=", "KB-WL"],
				["price_list", "=", "Standard Selling"],
				["selling", "=", 1],
				["price_list_rate", "is", "set"],
			],
		)
		address = {
			"doctype": "Address",
			"name": "",
			"title": "Address",
			"checks": [
				{
					"check_type": "exists_with_filter",
					"heading": "billing",
					"filter": [
						["Dynamic Link", "link_doctype", "=", "Customer"],
						["Dynamic Link", "link_name", "=", "Sunrise"],
						["address_type", "=", "Billing"],
					],
				}
			],
		}
		self.assertEqual(
			convert_entry(address)[0]["filters"],
			[
				["links.link_doctype", "=", "Customer"],
				["links.link_name", "=", "Sunrise"],
				["address_type", "=", "Billing"],
			],
		)

	def _run(self, rows):
		with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
			json.dump(rows, f)
		self.addCleanup(os.remove, f.name)
		out = StringIO()
		with redirect_stdout(out):
			run(f.name)
		return out.getvalue()

	def _row(self):
		entry = BOM | {
			"checks": [
				{
					"check_type": "child_has_row",
					"heading": "rows",
					"table": "items",
					"match": [{"item_code": "A"}, {"qty": 2}],
				}
			]
		}
		return {
			"name": "zz-import-test",
			"section": "ZZ Import Test",
			"checks": json.dumps({"BOM": [entry]}),
			"assignment_details": "hello",
		}

	def setUp(self):
		frappe.db.delete("Grader Section", {"name": "zz-import-test"})

	# Regression: a split v1 check was converted silently (commit b3f8cfb).
	def test_split_line_printed(self):
		out = self._run([self._row()])
		self.assertIn("SPLIT zz-import-test rows -> 2 checks (same-document requirement dropped)", out)

	# Regression: re-running the import overwrote edited sections (commit b3f8cfb).
	def test_rerun_leaves_existing_section_untouched(self):
		self._run([self._row()])
		before = frappe.get_doc("Grader Section", "zz-import-test")
		frappe.db.set_value("Grader Section", "zz-import-test", {"details": "<p>edited</p>", "published": 1})
		out = self._run([self._row()])
		self.assertIn("EXISTS zz-import-test", out)
		after = frappe.get_doc("Grader Section", "zz-import-test")
		self.assertEqual((after.details, after.published), ("<p>edited</p>", 1))
		self.assertEqual([c.check_id for c in after.checks], [c.check_id for c in before.checks])
