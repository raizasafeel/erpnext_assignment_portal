SETTINGS = "Grader Settings"
STUDENT_SITE = "Grader Student Site"
SECTION = "Grader Section"
CHECK = "Grader Check"
RUN = "Grader Run"
RUN_RESULT = "Grader Run Result"
ROLE = "Grader Manager"
OPERATORS = frozenset({"=", "!=", "like", "not like", "in", "not in", ">", "<", ">=", "<=", "is"})
RUN_ERRORS = ("unreachable", "timeout", "not_installed", "rejected", "bad_response", "internal")
CHECK_ERRORS = ("not_allowed", "invalid", "timeout")
DEFAULT_HOST_PATTERN = "*.m.frappe.cloud"
