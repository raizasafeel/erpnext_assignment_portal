import { describe, expect, it } from "vitest"

describe("boot", () => {
	it("reads the per-key globals jinjaBootData writes", async () => {
		Object.assign(window, { csrf_token: "t", site_name: "s", socketio_port: 9000 })
		const { boot } = await import("./boot")
		expect(boot).toEqual({ csrf_token: "t", site_name: "s", socketio_port: 9000 })
	})
})
