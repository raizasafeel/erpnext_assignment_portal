import frappe
from frappe import _

from erpnext_assignment_portal import linking, runs
from erpnext_assignment_portal.access import is_expired, require_enrolled
from erpnext_assignment_portal.constants import RUN, RUN_RESULT, SETTINGS, STUDENT_SITE

LINK_LIMIT = 10
LINK_WINDOW_SECONDS = 60 * 60
RUN_FIELDS = ["name", "status", "error_code", "started_on", "finished_on", "passed", "total"]


@frappe.whitelist()
def get_context() -> dict:
	user = frappe.session.user
	require_enrolled(user)
	site = frappe.db.get_value(
		STUDENT_SITE, {"student": user}, ["site", "status", "expires_on", "last_run"], as_dict=True
	)
	return {
		"user": user,
		"full_name": frappe.db.get_value("User", user, "full_name"),
		"site": {
			"site": site.site,
			"status": site.status,
			"expires_on": site.expires_on,
			"expired": is_expired(site),
			"revoked": site.status == "Revoked",
		}
		if site
		else None,
		"last_run": _run_dto(site.last_run) if site and site.last_run else None,
	}


@frappe.whitelist()
def get_sections() -> list[dict]:
	require_enrolled(frappe.session.user)
	sections, checks = runs.published(["title", "details"], ["check_id", "title"])
	return [
		{
			"slug": s.name,
			"title": s.title,
			"details": s.details,
			"checks": [{"check_id": c.check_id, "title": c.title} for c in checks if c.parent == s.name],
		}
		for s in sections
	]


@frappe.whitelist()
def get_run(run: str) -> dict:
	require_enrolled(frappe.session.user)
	if frappe.db.get_value(RUN, run, "student") != frappe.session.user:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return _run_dto(run)


@frappe.whitelist(methods=["POST"])
def link_site(site: str) -> dict:
	require_enrolled(frappe.session.user)
	_spend_link_attempt(frappe.session.user)
	name = linking.link_site(frappe.session.user, site)
	return {"site": frappe.db.get_value(STUDENT_SITE, name, "site")}


@frappe.whitelist(methods=["POST"])
def start_run() -> dict:
	require_enrolled(frappe.session.user)
	return {"run": runs.start_run(frappe.session.user)}


def _spend_link_attempt(user: str) -> None:
	cache = frappe.cache
	key = cache.make_key(f"grader-link-site:{user}")
	count = cache.incrby(key, 1)
	if count == 1 or cache.ttl(key) == -1:
		cache.expire(key, LINK_WINDOW_SECONDS)
	if count > LINK_LIMIT:
		frappe.throw(_("Too many link attempts. Try again later."), frappe.RateLimitExceededError)


def _run_dto(name: str) -> dict:
	dto = frappe.db.get_value(RUN, name, RUN_FIELDS, as_dict=True)
	dto["results"] = frappe.get_all(
		RUN_RESULT,
		filters={"parent": name, "parenttype": RUN},
		fields=["section", "check_id", "passed", "found_count", "check_error"],
		order_by="idx asc",
	)
	return dto
