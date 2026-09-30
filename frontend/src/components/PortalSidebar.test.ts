import { flushPromises, mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import PortalSidebar from "./PortalSidebar.vue"

vi.mock("frappe-ui", async () => {
	const { stub } = await import("../test/stub")
	const names = ["Dropdown", "ScrollArea", "Sidebar", "SidebarItem", "SidebarLabel", "TextInput"]
	return Object.fromEntries(names.map((n) => [n, stub(n)]))
})

const section = (slug: string, title: string, checks: number) => ({
	slug, title, details: "", checks: Array.from({ length: checks }, (_, i) => ({ check_id: `${slug}${i}`, title: "" })),
})
const SECTIONS = [section("company", "Company Setup", 4), section("wh", "Warehouses", 11), section("coa", "Chart of Accounts", 11)]
const SCORES = {
	company: { passed: 0, total: 4, percent: 0 },
	wh: { passed: 7, total: 11, percent: 64 },
	coa: { passed: 11, total: 11, percent: 100 },
}
const MENU = [{ label: "Apps", submenu: [] }, { label: "Log out" }]

function render() {
	return mount(PortalSidebar, {
		props: { sections: SECTIONS, scores: SCORES, active: "wh", fullName: "Grader Student", menu: MENU },
		global: { mocks: { __: (s: string) => s } },
	})
}
const items = (w: ReturnType<typeof render>) => w.findAllComponents({ name: "SidebarItem" })

describe("PortalSidebar", () => {
	it("lists every section with its score, status dot and active state", () => {
		const w = render()
		expect(items(w).map((i) => [i.vm.$attrs.label, i.find(".me-2").text(), i.vm.$attrs["data-status"]])).toEqual([
			["Company Setup", "0/4", "todo"],
			["Warehouses", "7/11", "partial"],
			["Chart of Accounts", "11/11", "done"],
		])
		expect(items(w).map((i) => i.find(".rounded-full").classes())).toEqual([
			expect.arrayContaining(["bg-surface-red-4"]),
			expect.arrayContaining(["bg-surface-amber-6"]),
			expect.arrayContaining(["bg-surface-green-7"]),
		])
		expect(items(w).map((i) => i.vm.$attrs.active)).toEqual([false, true, false])
	})
	it("filters sections by title", async () => {
		const w = render()
		w.findComponent({ name: "TextInput" }).vm.$emit("update:modelValue", "ware")
		await flushPromises()
		expect(items(w).map((i) => i.vm.$attrs.label)).toEqual(["Warehouses"])
		w.findComponent({ name: "TextInput" }).vm.$emit("update:modelValue", "zzz")
		await flushPromises()
		expect(w.text()).toContain("No matching sections")
	})
	it("emits pick when a section is clicked", async () => {
		const w = render()
		;(items(w)[2].vm.$attrs.onClick as () => void)()
		expect(w.emitted("pick")).toEqual([["coa"]])
	})
	it("hangs the user menu off the header", () => {
		const menu = render().findComponent({ name: "Dropdown" })
		expect(menu.text()).toContain("ERPNext Assignment Portal")
		expect(menu.text()).toContain("Grader Student")
		expect((menu.vm.$attrs.options as { label: string }[]).map((o) => o.label)).toEqual(["Apps", "Log out"])
	})
	it("sets sidebar text in the paragraph scale", () => {
		const w = render()
		expect(w.find(".text-p-base-medium").text()).toBe("ERPNext Assignment Portal")
		expect(w.findAll(".text-p-sm").map((e) => e.text())).toContain("7/11")
		expect(w.findComponent({ name: "TextInput" }).vm.$attrs.class).toBe("[&_input]:text-p-base")
	})
})
