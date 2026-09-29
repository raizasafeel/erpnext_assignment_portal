import { createRouter, createWebHistory } from "vue-router"

export default createRouter({
	history: createWebHistory("/assignments-portal/erpnext"),
	routes: [{ path: "/:section?", name: "portal", component: () => import("./pages/Portal.vue") }],
})
