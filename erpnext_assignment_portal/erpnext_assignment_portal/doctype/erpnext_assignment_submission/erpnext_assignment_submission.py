# Copyright (c) 2026, Raiza and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import now_datetime


class ERPNextAssignmentSubmission(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		passed_checks: DF.Int
		percent: DF.Percent
		results: DF.JSON | None
		section: DF.Link
		site: DF.Link
		status: DF.Literal["Passed", "Failed"]
		student: DF.Link | None
		submission_time: DF.Datetime | None
		total_checks: DF.Int
	# end: auto-generated types

	def autoname(self) -> None:
		time_now = now_datetime().strftime("%Y-%m-%d %H:%M:%S")
		self.name = f"{self.student}.{self.section}.{time_now}"

	def validate(self) -> None:
		if not self.submission_time:
			self.submission_time = now_datetime()
