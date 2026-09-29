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
	try:
		if canonical_site(site, frappe.get_single(SETTINGS).host_patterns()) != site:
			raise RemoteError("rejected")
	except frappe.ValidationError:
		raise RemoteError("rejected")
	host = urlparse(site).hostname
	path = f"/api/method/{method}"
	body = json.dumps(payload, separators=(",", ":")).encode()
	headers = {"Content-Type": "application/json", "Accept-Encoding": "identity", **sign(host, path, body)}
	try:
		response = requests.post(
			f"https://{host}{path}",
			data=body,
			headers=headers,
			timeout=(5, 30),
			allow_redirects=False,
			stream=True,
		)
	except requests.Timeout:
		raise RemoteError("timeout")
	except requests.RequestException:
		raise RemoteError("unreachable")
	with response:
		# frappe answers a method that isn't installed with 417 (handler.execute_cmd), not 404.
		if response.status_code == 417:
			raise RemoteError("not_installed")
		if response.status_code == 403:
			raise RemoteError("rejected")
		if response.status_code != 200:
			raise RemoteError("bad_response")
		try:
			raw = response.raw.read(MAX_RESPONSE_BYTES + 1)
		except ReadTimeoutError:
			raise RemoteError("timeout")
		except (HTTPError, requests.RequestException):
			raise RemoteError("unreachable")
	if len(raw) > MAX_RESPONSE_BYTES:
		raise RemoteError("bad_response")
	try:
		message = json.loads(raw).get("message")
	except (ValueError, AttributeError, RecursionError):
		raise RemoteError("bad_response")
	if not isinstance(message, dict):
		raise RemoteError("bad_response")
	return message
