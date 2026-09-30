import { describe, expect, it } from "vitest"
import { hasContent, withChecklistMarks } from "./details"

describe("hasContent", () => {
	it("treats an empty paragraph as no content", () => {
		expect(hasContent("<p></p>\n")).toBe(false)
		expect(hasContent("")).toBe(false)
	})
	it("counts text and tables", () => {
		expect(hasContent("<p>Do this</p>")).toBe(true)
		expect(hasContent("<table><tr><td></td></tr></table>")).toBe(true)
	})
})

describe("withChecklistMarks", () => {
	// Regression: checklist items rendered as TipTap checkboxes that looked clickable (commit e8ac13f).
	it("shows [ ] items as static box glyphs, never as form controls", () => {
		const html = withChecklistMarks("<ul>\n<li>[ ] Fiscal Year is active</li>\n<li>[x] <strong>Country</strong> is set</li>\n</ul>")
		const doc = new DOMParser().parseFromString(html, "text/html")
		expect(Array.from(doc.querySelectorAll("li")).map((li) => li.textContent)).toEqual([
			"\u2610 Fiscal Year is active",
			"\u2611 Country is set",
		])
		expect(doc.querySelector("input, [data-type]")).toBeNull()
	})
	it("leaves ordinary list items alone", () => {
		expect(withChecklistMarks("<ul><li>One</li></ul>")).toBe("<ul><li>One</li></ul>")
	})
})
