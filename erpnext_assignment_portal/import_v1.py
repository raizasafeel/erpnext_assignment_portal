import json

import frappe
from frappe.utils import md_to_html

from erpnext_assignment_portal.constants import SECTION
from erpnext_assignment_portal.erpnext_assignment_portal.doctype.grader_section.grader_section import (
	validate_filters,
)

MIXED_DETAILS = {
	"warehouses": "also holds the Users & Roles and Chart of Accounts text",
	"purchase-cycle": "ends with the Stock Transfer text (Inter-Warehouse Transfer)",
}


def normalise_filters(raw) -> list:
	if isinstance(raw, dict):
		return [[field, "=", value] for field, value in raw.items()]
	out = []
	for f in raw or []:
		if isinstance(f, list) and len(f) == 4 and f[0] == "Dynamic Link":
			out.append([f"links.{f[1]}", f[2], f[3]])
		else:
			out.append(list(f) if isinstance(f, list) else f)
	return out


def _base(entry: dict) -> list:
	if entry.get("filter"):
		return normalise_filters(entry["filter"])
	name = entry.get("name")
	if isinstance(name, list):
		return [["name", "in", name]]
	return [["name", "=", name]] if name else []


def _check(entry: dict, title: str, filters: list) -> dict:
	return {"title": title, "target_doctype": entry["doctype"], "filters": filters, "expected_min": 1}


def convert_entry(entry: dict) -> list[dict]:
	out = []
	for check in entry.get("checks", []):
		kind = check.get("check_type")
		title = check.get("heading") or entry.get("title") or entry["doctype"]
		if kind == "match":
			extra = [
				[f, "in" if isinstance(v, list) else "=", v]
				for pair in check.get("fields_to_match") or []
				for f, v in pair.items()
			]
			out.append(_check(entry, title, _base(entry) + extra))
		elif kind == "field_exists":
			out.append(
				_check(
					entry,
					title,
					_base(entry) + [[f, "is", "set"] for f in check.get("fields_to_match") or []],
				)
			)
		elif kind == "exists_with_filter":
			out.append(_check(entry, title, normalise_filters(check.get("filter"))))
		elif kind == "child_has_row":
			table = check.get("table", "rows")
			base = _base({"filter": check.get("filter") or entry.get("filter"), "name": entry.get("name")})
			matches = check.get("match") or [{}]
			for i, match in enumerate(matches, 1):
				child = [
					[
						f"{table}.{f}",
						"like" if isinstance(v, str) else "=",
						f"%{v}%" if isinstance(v, str) else v,
					]
					for f, v in match.items()
				]
				label = title if len(matches) == 1 else f"{title} ({i})"
				out.append(_check(entry, label, base + (child or [[f"{table}.name", "is", "set"]])))
		else:
			raise ValueError(f"unknown check_type {kind!r}")
	return out


def run(path: str) -> None:
	with open(path) as f:  # nosemgrep -- admin-run import; the path comes from the bench operator
		rows = json.load(f)
	for row in rows:
		checks, skipped = [], []
		for entries in json.loads(row.get("checks") or "{}").values():
			for entry in entries:
				try:
					converted = convert_entry(entry)
					for c in converted:
						validate_filters(c["filters"], c["title"])
				except (KeyError, ValueError, frappe.ValidationError) as e:
					skipped.append(f"{entry.get('title')}: {e}")
				else:
					checks += converted
		slug = row["name"].replace("&", "and")
		doc = frappe.get_doc(SECTION, slug) if frappe.db.exists(SECTION, slug) else frappe.new_doc(SECTION)
		doc.update(
			{
				"slug": slug,
				"title": row["section"],
				"order": row.get("section_order") or 0,
				"published": row.get("published") or 0,
				"details": md_to_html(row.get("assignment_details") or ""),
			}
		)
		doc.set("checks", [c | {"filters": json.dumps(c["filters"])} for c in checks])
		doc.save()
		print(f"{slug}: {len(checks)} checks")
		for s in skipped:
			print(f"  SKIPPED {s}")
		if not row.get("assignment_details"):
			print("  DETAILS EMPTY: write them by hand")
		if slug in MIXED_DETAILS:
			print(f"  DETAILS MIXED: {MIXED_DETAILS[slug]}; split them by hand")
	frappe.db.commit()  # nosemgrep: frappe-manual-commit -- one-off bench execute import; nothing else commits it
