from __future__ import annotations

import ipaddress
import json
import socket
from urllib.parse import urlparse

import frappe
import requests
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_days, get_datetime, now_datetime
from frappe.utils.password import (
	get_decrypted_password,
	set_encrypted_password,
)

TOKEN_REQUEST_DOCTYPE = "ERPNext Assignment Token Request"
STUDENT_SITE_DOCTYPE = "ERPNext Assignment Student Site"


def _normalize_site_url(url: str) -> str:
	parsed = urlparse(url.strip().rstrip("/"))
	scheme, host, path, port = parsed.scheme, parsed.hostname, parsed.path, parsed.port
	
	if not host:
		frappe.throw(_("Invalid site URL."))
	if scheme != "https":
		frappe.throw(_("Site URL must use https"))
	if path and path != "/":
		frappe.throw(_("Site URL must not include a path."))

	try:
		ip = ipaddress.ip_address(socket.gethostbyname(host))
		if not ip.is_global:
			frappe.throw(_("Site URL must be a public host."))
	except (socket.gaierror, ValueError):
		frappe.throw(_("Site URL must be a public host."))

	netloc = host if not port else f"{host}:{parsed.port}"
	return f"https://{netloc}"

def _get_settings():
	return frappe.get_cached_doc("ERPNext Assignment Portal Settings")


def _check_perms(user: str) -> None:
	"""Verify `user` is enrolled in the configured course. Caller must pass
	`frappe.session.user` from a non-`allow_guest` endpoint — the framework
	rejects Guest before our code runs."""
	settings = _get_settings()
	course = settings.course

	enrollment_filters = {"member": user, "course": course}
	if settings.restrict_to_paid_certification:
		enrollment_filters["purchased_certificate"] = 1

	if not course or not frappe.db.exists("LMS Enrollment", enrollment_filters):
		frappe.throw(
			(
				_("Paid certification is required to access the assignment portal.")
				if settings.restrict_to_paid_certification
				else _("{0} is not enrolled in this course.").format(user)
			),
			frappe.PermissionError,
		)
	if frappe.db.exists("LMS Certificate", {"member": user, "course": course}):
		frappe.throw(
			_("{0} has already completed this course.").format(user),
			frappe.PermissionError,
		)


def _site_state(user: str) -> dict | None:
	"""Student Site row + decrypted bearer + `valid` flag for `user`.

	Returns None if the student has no row. `valid` is true when the bearer
	is present, the URL is set, and the expiry is in the future.
	"""
	row = frappe.db.get_value(
		STUDENT_SITE_DOCTYPE,
		{"student": user},
		["name", "site", "last_checked", "token_expiry"],
		as_dict=True,
	)
	if not row:
		return None
	row.bearer = get_decrypted_password(
		STUDENT_SITE_DOCTYPE, row.name, "token_bearer", raise_exception=False
	)
	row.valid = bool(
		row.bearer
		and row.site
		and row.token_expiry
		and get_datetime(row.token_expiry) > now_datetime()
	)
	return row


@frappe.whitelist()
def get_current_user_info() -> dict:
	user = frappe.session.user
	state = _site_state(user)
	return {
		"user": user,
		"full_name": frappe.db.get_value("User", user, "full_name"),
		"course": _get_settings().course,
		"site": {
			"name": state.name,
			"site": state.site,
			"last_checked": state.last_checked,
			"connected": state.valid,
		} if state else None,
	}


@frappe.whitelist()
def get_assignments() -> list[dict]:
	return frappe.get_all(
		"ERPNext Assignment",
		filters={"published": 1},
		fields=["name", "section", "section_order", "blurb", "total_checks", "assignment_details"],
		order_by="section_order asc, section asc",
	)


@frappe.whitelist()
def get_my_submissions() -> list[dict]:
	user = frappe.session.user
	_check_perms(user)
	rows = frappe.get_all(
		"ERPNext Assignment Submission",
		filters={"student": user},
		fields=[
			"name",
			"section",
			"submission_time",
			"status",
			"passed_checks",
			"total_checks",
			"percent",
			"results",
		],
		order_by="submission_time desc",
	)
	for r in rows:
		try:
			r["results"] = json.loads(r.get("results") or "[]")
		except (TypeError, ValueError):
			r["results"] = []
	return rows


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=20, seconds=60 * 60)
def issue_token(site: str) -> dict:
	"""Demo site makes this call on app installation; we issue a 30 day token if student enrolled in course"""
	if not site:
		frappe.throw(_("Site URL is required."))
	site = _normalize_site_url(site)

	if frappe.db.exists(TOKEN_REQUEST_DOCTYPE, site):
		existing_expiry = frappe.db.get_value(TOKEN_REQUEST_DOCTYPE, site, ["token_expiry", "fulfilled"], as_dict=True)
		existing_token = get_decrypted_password(
			TOKEN_REQUEST_DOCTYPE, site, "token", raise_exception=False
		)
		if (
			existing_token
			and not existing_expiry.fulfilled
			and get_datetime(existing_expiry.token_expiry) > now_datetime()
		):
			return {"token": existing_token, "expires_at": existing_expiry.token_expiry}

		token = frappe.generate_hash(length=48)
		expiry = add_days(now_datetime(), 30)
		frappe.db.set_value(
			TOKEN_REQUEST_DOCTYPE,
			site,
			{"token_expiry": expiry, "fulfilled": 0},
		)
	else:
		token = frappe.generate_hash(length=48)
		expiry = add_days(now_datetime(), 30)
		frappe.get_doc(
			{
				"doctype": TOKEN_REQUEST_DOCTYPE,
				"site": site,
				"token_expiry": expiry,
				"fulfilled": 0,
			}
		).insert(ignore_permissions=True)

	set_encrypted_password(TOKEN_REQUEST_DOCTYPE, site, token, "token")
	return {"token": token, "expires_at": expiry}


@frappe.whitelist()
def register_site(site: str) -> dict:
	"""frontend call when student registers their demo site url: student claims token"""
	user = frappe.session.user
	_check_perms(user)
	
	if not site:
		frappe.throw(_("Site URL is required."))
	site = _normalize_site_url(site)

	owner = frappe.db.get_value(STUDENT_SITE_DOCTYPE, {"site": site}, "student")
	if owner and owner != user:
		frappe.throw(_("This site is already claimed by another student."))

	existing = _site_state(user)
	existing_bearer = existing.bearer if existing else None

	if existing_bearer and existing.site and existing.site != site:
		frappe.throw(_("Contact school@frappe.io to connect a different site."))

	if frappe.db.get_value(TOKEN_REQUEST_DOCTYPE, site, "fulfilled") == 0:
		token = get_decrypted_password(
			TOKEN_REQUEST_DOCTYPE, site, "token", raise_exception=False
		)
		expiry = frappe.db.get_value(TOKEN_REQUEST_DOCTYPE, site, "token_expiry")
		if not token:
			frappe.throw(_("Token request is missing its token. Reinstall the support app."))
	elif existing_bearer:
		token = existing_bearer
		expiry = add_days(now_datetime(), 30)
	else:
		frappe.throw(_("Install the grader support app on your demo first."))

	if existing:
		name = existing.name
		try:
			frappe.db.set_value(
				STUDENT_SITE_DOCTYPE,
				name,
				{"site": site, "token_expiry": expiry, "last_checked": now_datetime()},
			)
		except frappe.UniqueValidationError:
			frappe.throw(_("This site is already claimed by another student."))
	else:
		try:
			name = (
				frappe.get_doc(
					{
						"doctype": STUDENT_SITE_DOCTYPE,
						"student": user,
						"site": site,
						"token_expiry": expiry,
						"last_checked": now_datetime(),
					}
				)
				.insert(ignore_permissions=True)
				.name
			)
		except frappe.UniqueValidationError:
			frappe.throw(_("This site is already claimed by another student."))
	set_encrypted_password(STUDENT_SITE_DOCTYPE, name, token, "token_bearer")
	frappe.db.set_value(TOKEN_REQUEST_DOCTYPE, site, "fulfilled", 1)
	return {"name": name, "site": site}


@frappe.whitelist()
def disconnect_site() -> dict:
	user = frappe.session.user
	_check_perms(user)
	state = _site_state(user)
	if not state:
		return {"ok": True}

	# Keep site URL + bearer so the student can reconnect to the same demo
	# without reinstalling the support app. Only the expiry is cleared, which
	# is what flips `connected` to false in get_current_user_info.
	frappe.db.set_value(
		STUDENT_SITE_DOCTYPE,
		state.name,
		{"token_expiry": None, "last_checked": now_datetime()},
	)
	return {"ok": True}


@frappe.whitelist()
def regrade() -> dict:
	"""Re-check the whole connected site: grade every published section in one call."""
	user = frappe.session.user
	_check_perms(user)

	state = _site_state(user)
	if not state:
		frappe.throw(_("Install the grader support app on your demo first."))
	if not state.site:
		frappe.throw(_("Save your site URL first."))
	if not state.valid:
		frappe.throw(_("No valid token. Reinstall the grader support app to refresh."))

	frappe.enqueue(
		"erpnext_assignment_portal.erpnext_assignment_portal.api._run_grade",
		queue="short",
		job_name=f"grade-{user}",
		user=user,
		site_name=state.name,
		site_url=state.site,
	)
	return {"queued": True}


def _combined_checks() -> dict:
	"""Merge every published section's checks into one {section: entries} dict."""
	combined: dict = {}
	for row in frappe.get_all(
		"ERPNext Assignment", filters={"published": 1}, fields=["name", "checks"]
	):
		try:
			data = json.loads(row.checks or "{}")
		except (TypeError, ValueError):
			data = {}
		for section, entries in data.items():
			combined.setdefault(section, []).extend(entries or [])
	return combined


def _section_to_assignment() -> dict[str, str]:
	"""Map a section name -> its ERPNext Assignment docname."""
	return {
		r.section: r.name
		for r in frappe.get_all(
			"ERPNext Assignment", filters={"published": 1}, fields=["name", "section"]
		)
	}


def _submissions_from_results(results: list[dict]) -> dict[str, dict]:
	"""Group flat check results by their `section` tag into per-section summaries."""
	grouped: dict[str, dict] = {}
	for r in results:
		section = r.get("section") or "Other"
		g = grouped.setdefault(section, {"results": [], "passed": 0, "total": 0})
		g["results"].append(r)
		g["total"] += 1
		if r.get("passed"):
			g["passed"] += 1
	for g in grouped.values():
		total, passed = g["total"], g["passed"]
		g["percent"] = round(passed / total * 100, 1) if total else 0
		g["status"] = "Passed" if total and passed == total else "Failed"
	return grouped


def _run_grade(user: str, site_name: str, site_url: str) -> None:
	try:
		state = _site_state(user)
		if not state or not state.valid:
			_write_failed_submission(site_name, "No valid token. Reinstall the grader support app.")
			return
		token = state.bearer
		checks = _combined_checks()

		url = f"{site_url.rstrip('/')}/api/method/erpnext_assignment_checks.erpnext_assignment_checks.api.run_checks_api"
		try:
			resp = requests.post(
				url, headers={"X-Grader-Token": token}, json={"checks": checks}, timeout=30
			)
		except requests.ConnectionError:
			_write_failed_submission(site_name, f"Could not reach {site_url}.")
			return
		except requests.Timeout:
			_write_failed_submission(site_name, f"Request to {site_url} timed out.")
			return

		if resp.status_code >= 400:
			_write_failed_submission(site_name, f"Demo returned {resp.status_code}: {resp.text[:300]}")
			return
		try:
			result = resp.json().get("message") or {}
		except ValueError:
			_write_failed_submission(site_name, "Invalid response from demo.")
			return
	except Exception as e:
		_write_failed_submission(site_name, str(e) or e.__class__.__name__)
		return

	results = result.get("results") or []
	grouped = _submissions_from_results(results)
	section_map = _section_to_assignment()
	now = now_datetime()
	for section, g in grouped.items():
		assignment = section_map.get(section)
		if not assignment:
			continue
		# total_checks has fetch_from: "section.total_checks", so Frappe overwrites the
		# inserted value with the assignment's defined count on save. This is safe because
		# the live grader returns exactly one result per defined check, making g["total"]
		# equal to the assignment's total_checks.
		frappe.get_doc(
			{
				"doctype": "ERPNext Assignment Submission",
				"site": site_name,
				"section": assignment,
				"total_checks": g["total"],
				"passed_checks": g["passed"],
				"percent": g["percent"],
				"status": g["status"],
				"results": json.dumps(g["results"]),
			}
		).insert(ignore_permissions=True)
	frappe.db.set_value("ERPNext Assignment Student Site", site_name, "last_checked", now)
	frappe.db.commit()


def _write_failed_submission(site_name: str, error: str) -> None:
	error_row = [
		{"label": "Grading error", "passed": False,
		 "expected": "Grading completes successfully", "actual": error,
		 "section": "Grading", "title": "Grading"}
	]
	# Attach the error to the first published section so the student sees it.
	assignment = frappe.db.get_value(
		"ERPNext Assignment", {"published": 1}, "name", order_by="section_order asc"
	)
	if not assignment:
		return
	frappe.get_doc(
		{
			"doctype": "ERPNext Assignment Submission",
			"site": site_name,
			"section": assignment,
			"total_checks": 0,
			"passed_checks": 0,
			"percent": 0,
			"status": "Failed",
			"results": json.dumps(error_row),
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()
