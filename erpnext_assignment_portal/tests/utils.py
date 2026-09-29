import frappe

from erpnext_assignment_portal.constants import SETTINGS

COURSE = "grader-v2-test-course"


def ensure_settings() -> None:
	if not frappe.db.exists("LMS Course", COURSE):
		frappe.get_doc(
			{
				"doctype": "LMS Course",
				"name": COURSE,
				"title": "Grader v2 Test",
				"short_introduction": "x",
				"description": "x",
				"published": 1,
				"instructors": [{"instructor": "Administrator"}],
			}
		).insert(ignore_permissions=True, set_name=COURSE)
	frappe.db.set_single_value(SETTINGS, {"course": COURSE, "signing_key_id": "test"})


def make_student(email: str, enrolled: bool = True) -> str:
	if not frappe.db.exists("User", email):
		frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0]}).insert(
			ignore_permissions=True
		)
	if enrolled and not frappe.db.exists("LMS Enrollment", {"member": email, "course": COURSE}):
		frappe.get_doc({"doctype": "LMS Enrollment", "member": email, "course": COURSE}).insert(
			ignore_permissions=True
		)
	return email
