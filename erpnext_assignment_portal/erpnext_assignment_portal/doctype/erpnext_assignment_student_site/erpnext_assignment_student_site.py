# Copyright (c) 2026, Raiza and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ERPNextAssignmentStudentSite(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		last_checked: DF.Datetime | None
		site: DF.Data
		student: DF.Link
		token_bearer: DF.Password | None
	# end: auto-generated types

	pass
