import { mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import NotEnrolled from "./NotEnrolled.vue"

vi.mock("frappe-ui", async () => ({ Button: (await import("../test/stub")).stub("Button") }))

const COURSE = { name: "erpnext-basics", title: "ERPNext Basics" }

function render(course: typeof COURSE | null = COURSE) {
	return mount(NotEnrolled, {
		props: { course, user: "student@example.com" },
		global: { mocks: { __: (s: string, a: string[] = []) => s.replace("{0}", a[0] ?? "") } },
	})
}
const buttons = (w: ReturnType<typeof render>) => w.findAllComponents({ name: "Button" })

describe("NotEnrolled", () => {
	it("names the course and links to it", () => {
		const w = render()
		expect(w.text()).toContain("ERPNext Basics")
		expect(buttons(w)[0].vm.$attrs.href).toBe("/lms/courses/erpnext-basics")
	})
	it("falls back to generic copy without a course and still offers log out", async () => {
		const w = render(null)
		expect(w.text()).toContain("enrolled students")
		expect(buttons(w)).toHaveLength(1)
		await buttons(w)[0].vm.$emit("click")
		expect(w.emitted("logout")).toBeTruthy()
	})
})
