import frappe
from frappe import _
from frappe.utils import add_days, now_datetime

from erpnext_assignment_portal.constants import SETTINGS, STUDENT_SITE
from erpnext_assignment_portal.hosts import canonical_site
from erpnext_assignment_portal.remote import VERIFY_OWNER, RemoteError, post_signed


def link_site(user: str, url: str) -> str:
	settings = frappe.get_cached_doc(SETTINGS)
	site = canonical_site(url, settings.host_patterns())
	_confirm_owner(user, site)
	name = frappe.db.get_value(STUDENT_SITE, {"student": user}, "name", for_update=True)
	holder = frappe.db.get_value(STUDENT_SITE, {"site": site}, "student")
	if holder and holder != user:
		frappe.throw(_("This site is already linked to another student."))
	if name:
		doc = frappe.get_doc(STUDENT_SITE, name)
		doc.update({"site": site, "linked_on": now_datetime()})
	else:
		doc = _new_link(user, site, settings.default_link_days)
	return _save_link(doc, user, site)


def _confirm_owner(user: str, site: str) -> None:
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


def _new_link(user: str, site: str, link_days: int):
	doc = frappe.new_doc(STUDENT_SITE)
	doc.update(
		{
			"student": user,
			"site": site,
			"status": "Active",
			"linked_on": now_datetime(),
			"expires_on": add_days(now_datetime(), link_days) if link_days else None,
		}
	)
	return doc


def _save_link(doc, user: str, site: str) -> str:
	try:
		doc.save(ignore_permissions=True)
	except frappe.UniqueValidationError:
		frappe.clear_last_message()
		holder = frappe.db.get_value(STUDENT_SITE, {"site": site}, ["name", "student"], as_dict=True)
		if holder and holder.student == user:
			return holder.name
		if holder:
			frappe.throw(_("This site is already linked to another student."))
		frappe.throw(_("Something went wrong while linking. Try again."))
	return doc.name
