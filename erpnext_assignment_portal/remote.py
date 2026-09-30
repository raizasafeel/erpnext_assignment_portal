import json
from urllib.parse import urlparse

import frappe
import requests
from urllib3.exceptions import HTTPError, ReadTimeoutError

from erpnext_assignment_portal.constants import SETTINGS
from erpnext_assignment_portal.hosts import canonical_site
from erpnext_assignment_portal.signing import sign

VERIFY_OWNER = "erpnext_assignment_checks.api.verify_owner"
RUN_CHECKS = "erpnext_assignment_checks.api.run_checks"
MAX_RESPONSE_BYTES = 1024 * 1024


class RemoteError(Exception):
	def __init__(self, code: str):
		super().__init__(code)
		self.code = code


def post_signed(site: str, method: str, payload: dict) -> dict:
	_require_allowed(site)
	host = urlparse(site).hostname
	path = f"/api/method/{method}"
	body = json.dumps(payload, separators=(",", ":")).encode()
	headers = {"Content-Type": "application/json", "Accept-Encoding": "identity", **_sign(host, path, body)}
	return _message(_post(f"https://{host}{path}", body, headers))


def _require_allowed(site: str) -> None:
	try:
		allowed = canonical_site(site, frappe.get_cached_doc(SETTINGS).host_patterns()) == site
	except frappe.ValidationError:
		allowed = False
	if not allowed:
		raise RemoteError("rejected")


def _sign(host: str, path: str, body: bytes) -> dict[str, str]:
	try:
		return sign(host, path, body)
	except Exception:
		frappe.log_error("Grader request signing failed")
		raise RemoteError("internal")


def _post(url: str, body: bytes, headers: dict) -> bytes:
	try:
		response = requests.post(
			url, data=body, headers=headers, timeout=(5, 30), allow_redirects=False, stream=True
		)
	except requests.Timeout:
		raise RemoteError("timeout")
	except requests.RequestException:
		raise RemoteError("unreachable")
	with response:
		_check_status(response.status_code)
		try:
			return response.raw.read(MAX_RESPONSE_BYTES + 1)
		except ReadTimeoutError:
			raise RemoteError("timeout")
		except (HTTPError, requests.RequestException):
			raise RemoteError("unreachable")


def _check_status(status: int) -> None:
	# frappe answers a method that isn't installed with 417 (handler.execute_cmd), not 404.
	if status == 417:
		raise RemoteError("not_installed")
	if status == 403:
		raise RemoteError("rejected")
	if status != 200:
		raise RemoteError("bad_response")


def _message(raw: bytes) -> dict:
	if len(raw) > MAX_RESPONSE_BYTES:
		raise RemoteError("bad_response")
	try:
		message = json.loads(raw).get("message")
	except (ValueError, AttributeError, RecursionError):
		raise RemoteError("bad_response")
	if not isinstance(message, dict):
		raise RemoteError("bad_response")
	return message
