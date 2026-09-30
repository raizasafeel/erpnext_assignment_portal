import frappe

from erpnext_assignment_portal.constants import DEFAULT_HOST_PATTERN, ROLE, SETTINGS


def ensure_defaults() -> None:
	if not frappe.db.exists("Role", ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": ROLE, "desk_access": 1}).insert(
			ignore_permissions=True
		)
	settings = frappe.get_single(SETTINGS)
	if not settings.allowed_hosts:
		settings.append("allowed_hosts", {"pattern": DEFAULT_HOST_PATTERN})
		settings.flags.ignore_mandatory = True
		settings.save(ignore_permissions=True)
