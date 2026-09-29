import path from "path"
import vue from "@vitejs/plugin-vue"
import { defineConfig } from "vite"

export default defineConfig(async ({ mode }) => {
	const isDev = mode === "development"
	const frappeui = await importFrappeUIPlugin(isDev)

	return {
		define: {
			__VUE_PROD_HYDRATION_MISMATCH_DETAILS__: "false",
		},
		plugins: [
			frappeui({
				frappeProxy: true,
				lucideIcons: true,
				jinjaBootData: true,
				buildConfig: {
					indexHtmlPath: "../erpnext_assignment_portal/www/assignment_portal.html",
				},
			}),
			vue(),
		],
		server: {
			host: "0.0.0.0",
			allowedHosts: true,
		},
		resolve: {
			alias: {
				"@": path.resolve(__dirname, "src"),
				"tailwind.config.js": path.resolve(__dirname, "tailwind.config.js"),
			},
		},
		optimizeDeps: {
			include: [
				"feather-icons",
				"tailwind.config.js",
				"debug",
				"socket.io-client",
			],
			exclude: mode === "production" ? [] : ["frappe-ui"],
		},
	}
})

async function importFrappeUIPlugin(isDev) {
	if (isDev) {
		try {
			const module = await import("../frappe-ui/vite")
			return module.default
		} catch (error) {
			console.warn(
				"Local frappe-ui not found, falling back to npm package:",
				error.message,
			)
		}
	}
	const module = await import("frappe-ui/vite")
	return module.default
}
