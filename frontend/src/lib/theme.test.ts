import { readFileSync } from "node:fs"
import { resolve } from "node:path"
import { afterEach, describe, expect, it, vi } from "vitest"

const colorScheme = vi.hoisted(() => ({ setColorScheme: vi.fn(), calls: 0 }))
vi.mock("frappe-ui", () => ({
	useColorScheme: () => {
		colorScheme.calls += 1
		if (colorScheme.calls === 1) throw new Error("storage blocked")
		return { colorScheme: { value: "light" }, setColorScheme: colorScheme.setColorScheme }
	},
}))

import { useTheme } from "./theme"

const bootstrap = readFileSync(resolve(__dirname, "../../index.html"), "utf8").match(
	/<script>([\s\S]*?)<\/script>/,
)![1]

function paint(stored: string | null, osDark = false) {
	document.documentElement.removeAttribute("data-theme")
	vi.spyOn(Storage.prototype, "getItem").mockReturnValue(stored)
	window.matchMedia = vi.fn().mockReturnValue({ matches: osDark })
	new Function(bootstrap)()
	return document.documentElement.getAttribute("data-theme")
}

describe("theme bootstrap in index.html", () => {
	afterEach(() => vi.restoreAllMocks())
	it("applies a saved light or dark choice before the app loads", () => {
		expect(paint("dark")).toBe("dark")
		expect(paint("light", true)).toBe("light")
	})
	it("follows the OS for system or no saved choice", () => {
		expect(paint("system", true)).toBe("dark")
		expect(paint(null, false)).toBe("light")
	})
	it("survives storage that throws", () => {
		document.documentElement.removeAttribute("data-theme")
		vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
			throw new Error("blocked")
		})
		expect(() => new Function(bootstrap)()).not.toThrow()
	})
})

describe("useTheme", () => {
	it("recovers when storage throws on first use and on save", () => {
		colorScheme.setColorScheme.mockImplementation(() => {
			throw new Error("quota")
		})
		const theme = useTheme()
		expect(theme.colorScheme.value).toBe("light")
		expect(() => theme.setColorScheme("dark")).not.toThrow()
		expect(colorScheme.setColorScheme).toHaveBeenCalledWith("dark")
	})
})
