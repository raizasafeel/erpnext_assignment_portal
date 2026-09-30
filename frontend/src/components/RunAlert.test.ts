import { mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import RunAlert from "./RunAlert.vue"

vi.mock("frappe-ui", async () => ({ Alert: (await import("../test/stub")).stub("Alert") }))

const titles = (props: Record<string, unknown>) =>
	mount(RunAlert, {
		props: { run: null, expired: false, revoked: false, stillRunning: false, ...props },
		global: { mocks: { __: (s: string) => s } },
	})
		.findAll('[data-stub="Alert"]')
		.map((a) => a.attributes("data-title"))

describe("RunAlert", () => {
	// Regression: a revoked site showed the expired alert (commit 4da83d9).
	it("says a revoked site is revoked, not expired", () => {
		expect(titles({ revoked: true, expired: true })).toEqual(["Your site access was revoked"])
	})
	it("says an expired site has expired", () => {
		expect(titles({ expired: true })).toEqual(["Your site link has expired"])
	})
	it("shows nothing for an active site with no run", () => {
		expect(titles({})).toEqual([])
	})
})
