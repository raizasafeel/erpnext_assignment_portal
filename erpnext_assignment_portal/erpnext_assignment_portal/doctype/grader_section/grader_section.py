import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from erpnext_assignment_portal.constants import CHECK, MAX_CHECKS, OPERATORS, SECTION

SCALARS = (str, int, float)


class GraderSection(Document):
	def validate(self) -> None:
		ids = [c.check_id for c in self.checks if c.check_id]
		taken = set(
			frappe.get_all(
				CHECK,
				filters={
					"parenttype": SECTION,
					"parent": ["!=", self.name or ""],
					"check_id": ["in", ids or [""]],
				},
				pluck="check_id",
			)
		)
		for check in self.checks:
			if not check.check_id or check.check_id in taken:
				check.check_id = frappe.generate_hash(length=16)
			taken.add(check.check_id)
			validate_filters(check.filters, check.title)
			validate_bounds(check)
		if self.published:
			self.validate_check_limit()

	def validate_check_limit(self) -> None:
		others = frappe.get_all(
			SECTION, filters={"published": 1, "name": ["!=", self.name or ""]}, pluck="name"
		)
		sent = len(self.checks)
		if others:
			sent += frappe.db.count(CHECK, {"parenttype": SECTION, "parent": ["in", others]})
		if sent > MAX_CHECKS:
			frappe.throw(
				_("A run can send at most {0} checks. Unpublish a section or remove checks first.").format(
					MAX_CHECKS
				)
			)


def validate_bounds(check) -> None:
	if check.expected_min in (None, ""):
		check.expected_min = 1
	low, high = cint(check.expected_min), cint(check.expected_max)
	if low < 0:
		frappe.throw(_("Check {0}: the minimum can't be negative.").format(check.title))
	if high > 0 and low > high:
		frappe.throw(_("Check {0}: the minimum can't be greater than the maximum.").format(check.title))


def validate_filters(raw, title: str) -> None:
	try:
		filters = json.loads(raw) if isinstance(raw, str) else raw
	except ValueError:
		filters = None
	if not isinstance(filters, list) or not all(_valid(f) for f in filters):
		frappe.throw(_("Check {0}: filters must be a list of [field, operator, value].").format(title))


def _valid(f) -> bool:
	if not (isinstance(f, list) and len(f) == 3 and isinstance(f[0], str) and f[1] in OPERATORS):
		return False
	op, value = f[1], f[2]
	if op == "is":
		return value in ("set", "not set")
	if op in ("in", "not in"):
		return isinstance(value, list) and all(isinstance(v, SCALARS) for v in value)
	return isinstance(value, SCALARS)
