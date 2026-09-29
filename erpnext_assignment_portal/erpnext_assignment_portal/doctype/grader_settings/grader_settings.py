from frappe.model.document import Document


class GraderSettings(Document):
	def host_patterns(self) -> list[str]:
		return [row.pattern.strip().lower() for row in self.allowed_hosts if row.pattern]
