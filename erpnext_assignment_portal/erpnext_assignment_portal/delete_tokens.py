from __future__ import annotations

import frappe
from frappe.utils import now_datetime


def cleanup_unfulfilled_token_requests() -> None:
	"""Monthly: drop unfulfilled Token Requests whose tokens are past expiry.
	Fulfilled requests are kept indefinitely as an audit trail."""
	frappe.db.delete(
		"ERPNext Assignment Token Request",
		{"fulfilled": 0, "token_expiry": ["<", now_datetime()]},
	)
