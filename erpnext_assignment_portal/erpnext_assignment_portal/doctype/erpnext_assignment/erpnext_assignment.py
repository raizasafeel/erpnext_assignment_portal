# Copyright (c) 2026, Raiza and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document


class ERPNextAssignment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		assignment_details: DF.MarkdownEditor | None
		blurb: DF.SmallText | None
		checks: DF.JSON | None
		published: DF.Check
		section: DF.Data
		section_order: DF.Int
		total_checks: DF.Int
	# end: auto-generated types

	def autoname(self) -> None:
		# section is intentionally not DB-unique: same-named sections from different
		# source days stay distinct rows, disambiguated by the numeric suffix here.
		base = frappe.scrub(self.section or "").replace("_", "-")
		if not base:
			frappe.throw(_("Section is required."))
		self.name = base
		# First duplicate becomes base-2, then base-3, etc. (the original is #1).
		suffix = 2
		while frappe.db.exists("ERPNext Assignment", self.name):
			self.name = f"{base}-{suffix}"
			suffix += 1

	def validate(self) -> None:
		self._validate_mandatory()
		self.total_checks = _count_checks(self.checks)

		if not self.published:
			return

		if self.total_checks <= 0:
			frappe.throw(_("Published sections must have at least one grading check."))

		if not self.assignment_details:
			frappe.throw(_("Published sections must have assignment details."))


def _count_checks(checks_json: str | None) -> int:
	if not checks_json:
		return 0
	try:
		data = json.loads(checks_json)
	except (TypeError, ValueError):
		return 0
	if isinstance(data, dict):
		return sum(
			len(entry.get("checks", []))
			for entries in data.values()
			for entry in entries
		)
	if isinstance(data, list):
		return len(data)
	return 0
