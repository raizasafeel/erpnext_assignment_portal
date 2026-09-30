import { mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import HeroCard from "./HeroCard.vue"

vi.mock("frappe-ui", async () => {
	const { stub } = await import("../test/stub")
	return { Badge: stub("Badge"), Button: stub("Button") }
})

const OVERVIEW = { passed: 21, total: 106, percent: 20, sectionsDone: 1, sectionsTotal: 14 }

function render(props = {}) {
	return mount(HeroCard, {
		props: { fullName: "Grader Student", overview: OVERVIEW, grading: false, blocked: false, ...props },
		global: { mocks: { __: (s: string) => s } },
	})
}
const stat = (w: ReturnType<typeof render>, key: string) =>
	w.find(`[data-stat="${key}"]`).findAll("span").map((s) => s.text()).filter(Boolean)

describe("HeroCard", () => {
	it("greets the student by first name", () => {
		expect(render().find("h1").text()).toBe("Hi Grader, here's how your ERPNext site is doing")
	})
	it("explains the colours with a legend", () => {
		const labels = render()
			.findAllComponents({ name: "Badge" })
			.map((b) => b.attributes("label") ?? b.vm.$attrs.label)
		expect(labels).toEqual(["Green: done", "Red: needs work"])
	})
	it("shows passed, still to fix and sections done", () => {
		const w = render()
		expect(stat(w, "passed")).toEqual(["21", "Checks passed"])
		expect(stat(w, "to-fix")).toEqual(["85", "Still to fix"])
		expect(stat(w, "sections")).toEqual(["1/14", "Sections done"])
		expect(w.text()).toContain("21 of 106 checks passing")
		expect(w.find('[role="img"]').text()).toBe("20%")
	})
	it("changes the encouragement with progress", () => {
		expect(render().text()).toContain("Let's get started")
		expect(render({ overview: { ...OVERVIEW, passed: 106, percent: 100 } }).text()).toContain("All done")
	})
	it("disables Re-check for a blocked site and emits recheck otherwise", () => {
		expect(render({ blocked: true }).findComponent({ name: "Button" }).vm.$attrs.disabled).toBe(true)
		const w = render()
		;(w.findComponent({ name: "Button" }).vm.$attrs.onClick as () => void)()
		expect(w.emitted("recheck")).toHaveLength(1)
	})
})
