import { FrappeUI, frappeRequest, setConfig } from "frappe-ui"
import { createApp } from "vue"
import App from "./App.vue"
import { boot } from "./boot"
import router from "./router"
import { __ } from "./translate"
import "./index.css"

setConfig("resourceFetcher", frappeRequest)
setConfig("requestHeaders", { "X-Frappe-CSRF-Token": boot.csrf_token })
const app = createApp(App).use(router).use(FrappeUI)
app.config.globalProperties.__ = __
app.mount("#app")
