import { flushPromises, mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import SectionCard from "./SectionCard.vue"

vi.mock("frappe-ui", async () => {
	const { stub } = await import("../test/stub")
	return { Badge: stub("Badge"), LoadingText: stub("LoadingText") }
})
vi.mock("./SectionDetails.vue", async () => ({
	__esModule: true,
	default: (await import("../test/stub")).stub("SectionDetails"),
}))

const SECTION = {
	slug: "wh",
	title: "Warehouses",
	details: "<p>Create the warehouses.</p>",
	checks: [
		{ check_id: "1", title: "Mumbai: exists" },
		{ check_id: "2", title: "Pune: exists" },
		{ check_id: "3", title: "Stores: exists" },
		{ check_id: "4", title: "Transit: exists" },
	],
}
const result = (check_id: string, passed: number, check_error: string | null = null) => ({
	section: "wh", check_id, passed, found_count: passed, check_error,
})
const RUN = {
	name: "r", status: "Done", error_code: null, started_on: null, finished_on: null, passed: 1, total: 4,
	results: [result("1", 1), result("2", 0), result("3", 0, "not_allowed")],
}

function render(props = {}) {
	return mount(SectionCard, {
		props: { section: SECTION, index: 0, run: RUN, score: { passed: 1, total: 4, percent: 25 }, open: true, ...props },
		global: { mocks: { __: (s: string) => s } },
	})
}

describe("SectionCard", () => {
	it("numbers the section and badges its status", () => {
		const w = render()
		expect(w.find("button").text()).toContain("01")
		expect(w.findComponent({ name: "Badge" }).vm.$attrs).toMatchObject({ theme: "amber", label: "In progress · 1/4" })
		expect(render({ score: { passed: 4, total: 4, percent: 100 } }).findComponent({ name: "Badge" }).vm.$attrs.label).toBe("Done · 4/4")
	})
	it("marks each check passed, failed or not checked, with a check error label", () => {
		const rows = render().findAll("li")
		expect(rows.map((r) => r.attributes("data-state"))).toEqual(["pass", "fail", "fail", "pending"])
		expect(rows.map((r) => r.text().replace(/\s+/g, " "))).toEqual([
			"Passed: Mumbai: exists",
			"Not yet: Pune: exists",
			"Not yet: Stores: exists",
			"Not checked: Transit: exists",
		])
		expect(rows[2].findComponent({ name: "Badge" }).vm.$attrs.label).toBe("not allowed")
		expect(rows[1].findComponent({ name: "Badge" }).exists()).toBe(false)
	})
	it("shows nothing as checked for a run that errored", () => {
		const rows = render({ run: { ...RUN, status: "Error" } }).findAll("li")
		expect(rows.every((r) => r.attributes("data-state") === "pending")).toBe(true)
	})
	it("toggles from its header and reports aria-expanded", async () => {
		const open = render()
		expect(open.find("button").attributes("aria-expanded")).toBe("true")
		await open.find("button").trigger("click")
		expect(open.emitted("update:open")).toEqual([[false]])

		const closed = render({ open: false })
		expect(closed.find("button").attributes("aria-expanded")).toBe("false")
		expect(closed.find("#section-card-wh-body").attributes("style")).toContain("display: none")
		await closed.find("button").trigger("click")
		expect(closed.emitted("update:open")).toEqual([[true]])
	})
	it("loads the details only while open", async () => {
		expect(render({ open: false }).findComponent({ name: "SectionDetails" }).exists()).toBe(false)
		const w = render()
		await flushPromises()
		expect(w.findComponent({ name: "SectionDetails" }).vm.$attrs.html).toBe("<p>Create the warehouses.</p>")
	})
	it("says so when a section has no written instructions", () => {
		const w = render({ section: { ...SECTION, details: "<p></p>\n" } })
		expect(w.text()).toContain("There are no written instructions")
		expect(w.findComponent({ name: "SectionDetails" }).exists()).toBe(false)
	})
})
