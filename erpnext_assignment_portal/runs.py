import json
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from erpnext_assignment_portal.access import is_expired, require_enrolled
from erpnext_assignment_portal.constants import CHECK, CHECK_ERRORS, RUN, SECTION, SETTINGS, STUDENT_SITE
from erpnext_assignment_portal.remote import RUN_CHECKS, RemoteError, post_signed

STALE_MINUTES = 10
MAX_COUNT = 1000


def start_run(user: str) -> str:
	require_enrolled(user)
	site = _runnable_site(user)
	if site.last_run:
		active = _active_run_or_expire_stale(site.last_run)
		if active:
			return active
	_check_run_budget(user)
	run = frappe.get_doc({"doctype": RUN, "student": user, "student_site": site.name, "status": "Queued"})
	run.insert(ignore_permissions=True)
	frappe.db.set_value(STUDENT_SITE, site.name, "last_run", run.name)
	frappe.enqueue(
		"erpnext_assignment_portal.runs.execute_run",
		queue="short",
		job_id=f"grader-run::{run.name}",
		deduplicate=True,
		enqueue_after_commit=True,
		run_name=run.name,
	)
	return run.name


def _runnable_site(user: str) -> dict:
	site = frappe.db.get_value(
		STUDENT_SITE,
		{"student": user},
		["name", "status", "expires_on", "last_run"],
		as_dict=True,
		for_update=True,
	)
	if not site:
		frappe.throw(_("Link your trial site first."))
	if site.status == "Revoked":
		frappe.throw(_("Your site access was revoked. Contact the course staff to restore it."))
	if site.status != "Active" or is_expired(site):
		frappe.throw(_("Your site link has expired. Contact your instructor to extend it."))
	return site


def _check_run_budget(user: str) -> None:
	limit = frappe.db.get_single_value(SETTINGS, "run_rate_limit_per_hour") or 10
	since = now_datetime() - timedelta(hours=1)
	if frappe.db.count(RUN, {"student": user, "creation": (">", since)}) >= limit:
		frappe.throw(
			_("You have reached the hourly run limit. Try again later."), frappe.RateLimitExceededError
		)


def _active_run_or_expire_stale(name: str) -> str | None:
	run = frappe.db.get_value(RUN, name, ["status", "creation"], as_dict=True)
	if not run or run.status not in ("Queued", "Running"):
		return None
	if get_datetime(run.creation) > now_datetime() - timedelta(minutes=STALE_MINUTES):
		return name
	frappe.db.set_value(
		RUN, name, {"status": "Error", "error_code": "internal", "finished_on": now_datetime()}
	)
	return None


def published(section_fields: list[str], check_fields: list[str]) -> tuple[list, list]:
	sections = frappe.get_all(
		SECTION,
		filters={"published": 1},
		fields=["name", *section_fields],
		order_by="`tabGrader Section`.`order` asc",
	)
	checks = frappe.get_all(
		CHECK,
		filters={"parenttype": SECTION, "parent": ["in", [s.name for s in sections] or [""]]},
		fields=["parent", *check_fields],
		order_by="idx asc",
	)
	return sections, checks


def published_checks() -> list:
	sections, checks = published(
		[], ["check_id", "target_doctype", "filters", "expected_min", "expected_max"]
	)
	by_section = {s.name: [] for s in sections}
	for check in checks:
		check.section = check.pop("parent")
		check.filters = json.loads(check.filters or "[]")
		by_section[check.section].append(check)
	return [check for s in sections for check in by_section[s.name]]


def execute_run(run_name: str) -> None:
	run = frappe.get_doc(RUN, run_name)
	if run.status != "Queued":
		return
	run.db_set({"status": "Running", "started_on": now_datetime()})
	frappe.db.commit()  # nosemgrep: frappe-manual-commit -- publish Running; drop the row lock before the outbound call
	try:
		_execute(run)
	except RemoteError as e:
		_finish(run, error_code=e.code)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(f"Grader run {run_name} failed")
		_finish(run, error_code="internal")


def _execute(run) -> None:
	sent = published_checks()
	site = frappe.db.get_value(STUDENT_SITE, run.student_site, "site")
	payload = {
		"checks": [
			{"check_id": c.check_id, "target_doctype": c.target_doctype, "filters": c.filters} for c in sent
		]
	}
	rows = evaluate(sent, post_signed(site, RUN_CHECKS, payload).get("results"))
	_finish(run, rows=rows)


def evaluate(sent: list, results) -> list[dict]:
	if not isinstance(results, list):
		raise RemoteError("bad_response")
	by_id = {}
	for r in results:
		if not isinstance(r, dict) or not isinstance(r.get("check_id"), str) or r["check_id"] in by_id:
			raise RemoteError("bad_response")
		by_id[r["check_id"]] = r
	if set(by_id) != {c.check_id for c in sent}:
		raise RemoteError("bad_response")
	return [_row(c, by_id[c.check_id]) for c in sent]


def _row(check, result: dict) -> dict:
	row = {"section": check.section, "check_id": check.check_id}
	if "error" in result:
		if result["error"] not in CHECK_ERRORS:
			raise RemoteError("bad_response")
		return row | {"found_count": 0, "check_error": result["error"], "passed": 0}
	count = result.get("found_count")
	if not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= MAX_COUNT:
		raise RemoteError("bad_response")
	passed = count >= check.expected_min and (not check.expected_max or count <= check.expected_max)
	return row | {"found_count": count, "check_error": None, "passed": int(passed)}


def _finish(run, rows: list | None = None, error_code: str | None = None) -> None:
	run.reload()
	run.finished_on = now_datetime()
	if error_code:
		run.status, run.error_code = "Error", error_code
	else:
		run.status = "Done"
		run.set("results", rows)
		run.total = len(rows)
		run.passed = sum(r["passed"] for r in rows)
	run.save(ignore_permissions=True)
	frappe.publish_realtime(
		"grader_run", {"run": run.name, "status": run.status}, user=run.student, after_commit=True
	)
