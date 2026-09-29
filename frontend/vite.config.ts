import path from "node:path"
import vue from "@vitejs/plugin-vue"
import frappeui from "frappe-ui/vite"
import { defineConfig } from "vite"

export default defineConfig({
	plugins: [
		frappeui({
			frontendRoute: "/assignments-portal/erpnext",
			frappeProxy: true,
			lucideIcons: true,
			jinjaBootData: true,
			buildConfig: { indexHtmlPath: "../erpnext_assignment_portal/www/assignment_portal.html" },
		}),
		vue(),
	],
	resolve: { alias: { "@": path.resolve(__dirname, "src") } },
	test: { environment: "jsdom" },
})
