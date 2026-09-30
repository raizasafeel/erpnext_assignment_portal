import { describe, expect, it } from "vitest"
import { hasContent, withTaskLists } from "./details"

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

describe("withTaskLists", () => {
	it("turns a [ ] checklist into a task list", () => {
		const out = new DOMParser().parseFromString(
			withTaskLists("<ul>\n<li>[ ] Fiscal Year is active</li>\n<li>[x] <strong>Country</strong> is set</li>\n</ul>"),
			"text/html",
		)
		const items = Array.from(out.querySelectorAll('ul[data-type="taskList"] > li[data-type="taskItem"]'))
		expect(items.map((li) => [li.getAttribute("data-checked"), li.textContent?.trim()])).toEqual([
			["false", "Fiscal Year is active"],
			["true", "Country is set"],
		])
	})
	it("leaves an ordinary list alone", () => {
		const html = "<ul><li>One</li><li>[ ] Two</li></ul>"
		expect(withTaskLists(html)).toBe(html)
	})
})
