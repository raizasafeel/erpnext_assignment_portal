import { flushPromises, mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import LinkSiteForm from "./LinkSiteForm.vue"

const linkSite = vi.fn()
vi.mock("../api", () => ({ linkSite: (s: string) => linkSite(s) }))
vi.mock("frappe-ui", async () => {
	const { stub } = await import("../test/stub")
	return { Button: stub("Button"), ErrorMessage: stub("ErrorMessage"), FormControl: stub("FormControl") }
})

function render() {
	return mount(LinkSiteForm, { global: { mocks: { __: (s: string) => s } } })
}
const button = (w: ReturnType<typeof render>) => w.findComponent({ name: "Button" })

describe("LinkSiteForm", () => {
	it("keeps Connect disabled until an address is typed", async () => {
		const w = render()
		expect(button(w).vm.$attrs.disabled).toBe(true)
		await w.findComponent({ name: "FormControl" }).vm.$emit("update:modelValue", "https://a.m.frappe.cloud")
		expect(button(w).vm.$attrs.disabled).toBe(false)
	})
	it("submits the trimmed address on Enter and emits linked", async () => {
		linkSite.mockResolvedValue({ site: "https://a.m.frappe.cloud" })
		const w = render()
		await w.findComponent({ name: "FormControl" }).vm.$emit("update:modelValue", " https://a.m.frappe.cloud ")
		await w.find("form").trigger("submit")
		await flushPromises()
		expect(linkSite).toHaveBeenCalledWith("https://a.m.frappe.cloud")
		expect(w.emitted("linked")).toBeTruthy()
	})
})
