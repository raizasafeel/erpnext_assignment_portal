import re
from fnmatch import fnmatchcase
from urllib.parse import urlparse

import frappe
from frappe import _

DNS_HOST = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


def canonical_site(url: str, patterns: list[str]) -> str:
	invalid = _("Enter your trial site's address, like https://yourname.m.frappe.cloud")
	parsed = None
	try:
		parsed = urlparse(url.strip() if isinstance(url, str) else "")
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
	if len(host) > 253 or not DNS_HOST.fullmatch(host):
		frappe.throw(invalid)
	if not any(fnmatchcase(host, p) for p in patterns):
		frappe.throw(_("Only Frappe Cloud trial sites can be linked."))
	return f"https://{host}"
