from fnmatch import fnmatchcase
from urllib.parse import urlparse

import frappe
from frappe import _


def canonical_site(url: str, patterns: list[str]) -> str:
	invalid = _("Enter your trial site's address, like https://yourname.m.frappe.cloud")
	parsed = None
	try:
		parsed = urlparse((url or "").strip())
		port = parsed.port
	except ValueError:
		frappe.throw(invalid)
	host = (parsed.hostname or "").rstrip(".").lower()
	if (
		parsed.scheme != "https"
		or not host
		or port not in (None, 443)
		or parsed.path not in ("", "/")
		or parsed.query
		or parsed.username
		or parsed.password
	):
		frappe.throw(invalid)
	if not any(fnmatchcase(host, p) for p in patterns):
		frappe.throw(_("Only Frappe Cloud trial sites can be linked."))
	return f"https://{host}"
