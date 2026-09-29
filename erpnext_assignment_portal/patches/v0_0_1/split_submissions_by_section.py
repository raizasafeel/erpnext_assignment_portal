from __future__ import annotations

import json

import frappe


def execute() -> None:
	if not frappe.db.exists("DocType", "ERPNext Assignment Submission"):
		return
	rows = frappe.get_all(
		"ERPNext Assignment Submission",
		fields=["name", "site", "student", "section", "submission_time", "results"],
	)
	for row in rows:
		try:
			results = json.loads(row.results or "[]")
		except (TypeError, ValueError):
			results = []
		by_section: dict[str, list] = {}
		for r in results:
			by_section.setdefault(r.get("section") or row.section, []).append(r)
		# Rows already covering a single section are left untouched — this is what
		# makes re-runs no-ops (split rows have len == 1 and are skipped).
		if len(by_section) <= 1:
			# Re-point a stale/dangling single-section link (e.g. a legacy failed-grade row whose
			# `section` still holds a day docname B1 deleted) to a valid assignment. Idempotent:
			# a row already pointing at its correct section resolves to the same target (no-op).
			only = next(iter(by_section)) if by_section else None
			target = frappe.scrub(only).replace("_", "-") if only else None
			if not target or not frappe.db.exists("ERPNext Assignment", target):
				target = row.section if (row.section and frappe.db.exists("ERPNext Assignment", row.section)) else None
			if not target:
				target = frappe.db.get_value("ERPNext Assignment", {"published": 1}, "name", order_by="section_order asc")
			if target and target != row.section:
				frappe.db.set_value("ERPNext Assignment Submission", row.name, "section", target, update_modified=False)
			continue
		for sec_name, sec_results in by_section.items():
			# Match B1's autoname transform: frappe.scrub(section).replace("_", "-").
			# Fall back to the row's own section link if the scrubbed name has no row.
			assignment = frappe.scrub(sec_name).replace("_", "-") if sec_name else row.section
			if not frappe.db.exists("ERPNext Assignment", assignment):
				assignment = row.section
			# total_checks is fetch_from section.total_checks, so base status/percent on the section's count to keep the row self-consistent.
			section_total = frappe.db.get_value("ERPNext Assignment", assignment, "total_checks")
			total = section_total or len(sec_results)
			passed = sum(1 for r in sec_results if r.get("passed"))
			doc = frappe.get_doc(
				{
					"doctype": "ERPNext Assignment Submission",
					"site": row.site,
					"student": row.student,  # also populated via fetch_from: site.student; kept as an explicit default
					"section": assignment,
					"submission_time": row.submission_time,
					"total_checks": total,
					"passed_checks": passed,
					"percent": round(passed / total * 100, 1) if total else 0,
					"status": "Passed" if total and passed == total else "Failed",
					"results": frappe.as_json(sec_results),
				}
			)
			# The controller autoname is `{student}.{section}.{now}` — keyed on the
			# *current* time, so the many same-second inserts this split produces would
			# collide on PRIMARY. Name explicitly from the (distinct) submission_time,
			# matching the original per-day naming scheme, and disambiguate on the rare
			# tie (same student+section+second) with a numeric suffix.
			base = f"{row.student}.{assignment}.{row.submission_time}"
			name = base
			suffix = 2
			while frappe.db.exists("ERPNext Assignment Submission", name):
				name = f"{base}-{suffix}"
				suffix += 1
			doc.insert(ignore_permissions=True, set_name=name)
		frappe.delete_doc(
			"ERPNext Assignment Submission", row.name, ignore_permissions=True, force=True
		)
	# No frappe.db.commit() — the patch runner commits; omitting keeps the patch
	# rollback-safe under FrappeTestCase.
