import re
from fnmatch import fnmatchcase
from urllib.parse import urlparse

import frappe
from frappe import _

DNS_HOST = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


def canonical_site(url: str, patterns: list[str]) -> str:
	host = _https_host(url)
	if not host:
		frappe.throw(_("Enter your trial site's address, like https://yourname.m.frappe.cloud"))
	if not any(fnmatchcase(host, p) for p in patterns):
		frappe.throw(_("Only Frappe Cloud trial sites can be linked."))
	return f"https://{host}"


def _https_host(url: str) -> str | None:
	try:
		parsed = urlparse(url.strip() if isinstance(url, str) else "")
		port = parsed.port
	except ValueError:
		return None
	host = (parsed.hostname or "").rstrip(".").lower()
	if parsed.scheme != "https" or port not in (None, 443) or parsed.path not in ("", "/"):
		return None
	if parsed.query or parsed.username or parsed.password:
		return None
	if len(host) > 253 or not DNS_HOST.fullmatch(host):
		return None
	return host
