from frappe.tests import IntegrationTestCase

from erpnext_assignment_portal.import_v1 import convert_entry

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
