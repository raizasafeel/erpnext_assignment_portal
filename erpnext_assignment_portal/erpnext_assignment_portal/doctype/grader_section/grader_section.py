import json

import frappe
from frappe import _
from frappe.model.document import Document

from erpnext_assignment_portal.constants import OPERATORS

SCALARS = (str, int, float)


class GraderSection(Document):
	def validate(self) -> None:
		for check in self.checks:
			if not check.check_id:
				check.check_id = frappe.generate_hash(length=16)
			validate_filters(check.filters, check.title)


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
