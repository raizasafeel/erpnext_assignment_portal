import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from erpnext_assignment_portal.constants import SETTINGS


def is_enrolled(user: str) -> bool:
	course = frappe.db.get_single_value(SETTINGS, "course")
	return bool(course) and bool(frappe.db.exists("LMS Enrollment", {"member": user, "course": course}))


def require_enrolled(user: str) -> None:
	if not is_enrolled(user):
		frappe.throw(_("You are not enrolled in this course."), frappe.PermissionError)


def is_expired(site) -> bool:
	return bool(site.get("expires_on")) and get_datetime(site.get("expires_on")) <= now_datetime()
