from __future__ import annotations

import json
import re

import frappe
from erpnext_assignment_portal.erpnext_assignment_portal.doctype.erpnext_assignment.erpnext_assignment import (
	_count_checks,
)


def slice_markdown(md: str | None, sections: list[str]) -> dict[str, str]:
	"""Split assignment markdown by `#`/`##` headings, mapping each block to the
	section whose name matches the heading (normalized). Lines before the first
	matched heading, and any unmatched-heading blocks, attach to the current
	(previous matched) section. Returns {section: markdown}."""
	out: dict[str, str] = {s: "" for s in sections}
	if not md:
		return out
	def norm(t: str) -> str:
		return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()
	by_norm = {norm(s): s for s in sections}
	current: str | None = None
	for line in md.splitlines(keepends=True):
		m = re.match(r"^\s{0,3}#{1,6}\s+(.*)$", line)
		if m:
			heading = norm(m.group(1))
			matched = by_norm.get(heading)
			if not matched:
				# Loose substring fallback: maps reworded/singular-vs-plural headings to their
				# section (e.g. a `## Customer` heading → the "Customers" section).
				for n, s in by_norm.items():
					if n and (n in heading or heading in n):
						matched = s
						break
			if matched:
				current = matched
		if current:
			out[current] += line
	return out


def execute() -> None:
	if not frappe.db.exists("DocType", "ERPNext Assignment"):
		return

	# order_by="creation asc" so section_order is a stable sequential seed (best-effort, not unique-guaranteed).
	rows = frappe.get_all(
		"ERPNext Assignment",
		fields=["name", "section", "section_order", "published", "assignment_details", "checks"],
		order_by="creation asc",
	)
	order = frappe.db.count("ERPNext Assignment")  # running order seed for new rows
	for row in rows:
		try:
			data = json.loads(row.checks or "{}")
		except (TypeError, ValueError):
			data = {}
		if not isinstance(data, dict) or not data:
			continue

		if len(data) == 1:
			# Already a single-section row. Backfill its `section` from the key if unset.
			only_key = next(iter(data))
			if not row.section or row.section != only_key:
				frappe.db.set_value(
					"ERPNext Assignment", row.name, "section", only_key, update_modified=False
				)
			continue

		section_names = list(data.keys())
		slices = slice_markdown(row.assignment_details, section_names)
		for idx, sec in enumerate(section_names):
			# Idempotency: content-keyed skip is a partial-failure-recovery guard — re-running after an
			# interrupted migration won't duplicate already-created section rows. Section names are unique
			# across source days, so the "suffix on collision; do not merge" dedup decision is unaffected.
			already = any(
				json.loads(e.checks or "{}") == {sec: data[sec]}
				for e in frappe.get_all(
					"ERPNext Assignment", filters={"section": sec}, fields=["name", "checks"]
				)
			)
			if already:
				continue
			checks_json = frappe.as_json({sec: data[sec]})
			doc = frappe.get_doc(
				{
					"doctype": "ERPNext Assignment",
					"section": sec,
					"section_order": order + idx,
					"published": row.published,
					"assignment_details": slices.get(sec) or "",
					"checks": checks_json,
					# validate() is skipped below, so set total_checks here as its only writer.
					"total_checks": _count_checks(checks_json),
				}
			)
			# Bypass validate() so we can migrate pre-existing published sections whose
			# source day-markdown has no per-section heading (empty sliced details).
			# total_checks is set above because validate() — its only writer — is skipped.
			doc.flags.ignore_validate = True
			doc.insert(ignore_permissions=True)
		order += len(section_names)
		frappe.delete_doc("ERPNext Assignment", row.name, ignore_permissions=True, force=True)
	# NOTE: no frappe.db.commit() here — the Frappe patch runner commits after the
	# patch, and omitting it keeps the patch rollback-safe under FrappeTestCase.
