app_name = "erpnext_assignment_portal"
app_title = "ERPNext Assignment Portal"
app_publisher = "Raiza"
app_description = "Grader for erpnext assignment on frappe school"
app_email = "raizasafeel@gmail.com"
app_license = "mit"

required_apps = ["lms"]

add_to_apps_screen = [
	{
		"name": "erpnext_assignment_portal",
		"logo": "/assets/erpnext_assignment_portal/images/portal-logo.svg",
		"title": "Assignment Portal",
		"route": "/assignments-portal/erpnext",
	}
]

website_route_rules = [
	{"from_route": "/assignments-portal/erpnext", "to_route": "assignment_portal"},
	{"from_route": "/assignments-portal/erpnext/<path:app_path>", "to_route": "assignment_portal"},
]

after_install = "erpnext_assignment_portal.setup.ensure_defaults"
after_migrate = "erpnext_assignment_portal.setup.ensure_defaults"

export_python_type_annotations = True

require_type_annotated_api_methods = True
