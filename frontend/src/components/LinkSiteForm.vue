<template>
	<form class="flex flex-col gap-3" @submit.prevent="submit">
		<FormControl
			v-model="site"
			type="url"
			:label="__('Site address')"
			placeholder="https://yourname.m.frappe.cloud"
			:description="
				__('You must be a System Manager on this site with the email you use here.')
			"
			autocomplete="url"
		/>
		<ErrorMessage :message="error" />
		<Button
			type="submit"
			variant="solid"
			class="w-full"
			:loading="loading"
			:disabled="!site.trim()"
			:label="__('Connect site')"
		/>
	</form>
</template>

<script setup lang="ts">
import { Button, ErrorMessage, FormControl } from "frappe-ui";
import { ref } from "vue";
import { linkSite } from "../api";
import { requestErrorMessage } from "../lib/errors";

const props = defineProps<{ defaultSite?: string }>();
const emit = defineEmits<{ linked: [] }>();
const site = ref(props.defaultSite ?? "");
const loading = ref(false);
const error = ref("");

async function submit() {
	loading.value = true;
	error.value = "";
	try {
		await linkSite(site.value.trim());
		emit("linked");
	} catch (e) {
		error.value = requestErrorMessage(e);
	} finally {
		loading.value = false;
	}
}
</script>
