import { readFileSync } from "node:fs"
import { describe, expect, it } from "vitest"

const read = (path: string) => readFileSync(new URL(path, import.meta.url), "utf8")

describe("frappe-ui version", () => {
	it("is pinned to exactly 1.0.0-rc.1", () => {
		expect(JSON.parse(read("../package.json")).dependencies["frappe-ui"]).toBe("1.0.0-rc.1")
	})
	it("is locked to 1.0.0-rc.1", () => {
		expect(read("../yarn.lock")).toMatch(/^"?frappe-ui@1\.0\.0-rc\.1"?:\n\s+version "1\.0\.0-rc\.1"/m)
	})
	it("is installed at 1.0.0-rc.1", () => {
		const installed = JSON.parse(read("../node_modules/frappe-ui/package.json")).version
		console.log(`frappe-ui installed: ${installed}`)
		expect(installed).toBe("1.0.0-rc.1")
	})
})
