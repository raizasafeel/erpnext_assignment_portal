import frappe
from frappe.translate import get_user_lang
from frappe.utils.jinja_globals import is_rtl

no_cache = 1
ROUTE = "/assignments-portal/erpnext"


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = f"/login?redirect-to={ROUTE}"
		raise frappe.Redirect

	csrf_token = frappe.sessions.get_csrf_token()

	context.csrf_token = csrf_token
	context.boot = get_boot(csrf_token)
	context.favicon = (
		frappe.db.get_single_value("Website Settings", "favicon")
		or "/assets/erpnext_assignment_portal/images/logo.svg"
	)
	context.title = frappe.db.get_single_value("Website Settings", "app_name") or "ERPNext Assignment Portal"
	return context


def get_boot(csrf_token: str) -> frappe._dict:
	return frappe._dict(
		{
			"frappe_version": frappe.__version__,
			"read_only_mode": frappe.flags.read_only,
			"csrf_token": csrf_token,
			"site_name": frappe.local.site,
			"socketio_port": frappe.conf.socketio_port,
			"lang": get_user_lang(),
			"text_direction": "rtl" if is_rtl() else "ltr",
		}
	)
