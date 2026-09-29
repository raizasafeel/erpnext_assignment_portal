import frappe
from frappe import _
from frappe.utils import add_days, now_datetime

from erpnext_assignment_portal.access import require_enrolled
from erpnext_assignment_portal.constants import SETTINGS, STUDENT_SITE
from erpnext_assignment_portal.hosts import canonical_site
from erpnext_assignment_portal.remote import VERIFY_OWNER, RemoteError, post_signed


def link_site(user: str, url: str) -> str:
	require_enrolled(user)
	settings = frappe.get_single(SETTINGS)
	site = canonical_site(url, settings.host_patterns())
	email = frappe.db.get_value("User", user, "email")
	try:
		ok = post_signed(site, VERIFY_OWNER, {"email": email}).get("ok") is True
	except RemoteError:
		ok = False
	if not ok:
		frappe.throw(
			_(
				"We couldn't confirm you own this site. Log in to it as a System Manager with {0}, and make sure the grader app is installed."
			).format(email)
		)
	name = frappe.db.get_value(STUDENT_SITE, {"student": user}, "name", for_update=True)
	holder = frappe.db.get_value(STUDENT_SITE, {"site": site}, "student")
	if holder and holder != user:
		frappe.throw(_("This site is already linked to another student."))
	if name:
		doc = frappe.get_doc(STUDENT_SITE, name)
		doc.update({"site": site, "linked_on": now_datetime()})
	else:
		doc = frappe.new_doc(STUDENT_SITE)
		doc.update(
			{
				"student": user,
				"site": site,
				"status": "Active",
				"linked_on": now_datetime(),
				"expires_on": add_days(now_datetime(), settings.default_link_days)
				if settings.default_link_days
				else None,
			}
		)
	logged = len(frappe.local.message_log)
	try:
		doc.save(ignore_permissions=True)
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		del frappe.local.message_log[logged:]
		holder = frappe.db.get_value(STUDENT_SITE, {"site": site}, "student")
		if holder and holder != user:
			frappe.throw(_("This site is already linked to another student."))
		frappe.throw(_("Something went wrong while linking. Please try again."))
	return doc.name
