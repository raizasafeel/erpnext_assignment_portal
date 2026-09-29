import base64
import hashlib
import time

import frappe
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from frappe import _

from erpnext_assignment_portal.constants import SETTINGS


def signing_message(host: str, timestamp: str, path: str, body: bytes) -> bytes:
	return f"{host}\n{timestamp}\n{path}\n{hashlib.sha256(body).hexdigest()}".encode()


def sign(host: str, path: str, body: bytes, now: float | None = None) -> dict[str, str]:
	pem = frappe.conf.get("grader_signing_key")
	key_id = frappe.db.get_single_value(SETTINGS, "signing_key_id")
	if not pem or not key_id:
		frappe.throw(_("Grader signing key is not configured."))
	timestamp = str(int(time.time() if now is None else now))
	signature = load_pem_private_key(pem.encode(), password=None).sign(
		signing_message(host, timestamp, path, body)
	)
	return {
		"X-Grader-Key-Id": key_id,
		"X-Grader-Timestamp": timestamp,
		"X-Grader-Signature": base64.b64encode(signature).decode(),
	}
