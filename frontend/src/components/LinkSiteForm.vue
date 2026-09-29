<template>
	<div class="mx-auto flex w-full max-w-md flex-col gap-4 p-6">
		<h1 class="text-xl font-semibold text-ink-gray-9">
			{{ __("Link your trial site") }}
		</h1>
		<p class="text-p-base text-ink-gray-7">
			{{
				__(
					"Install the ERPNext Assignment Checks app on your Frappe Cloud trial, then enter its address. You must be a System Manager there with this email."
				)
			}}
		</p>
		<FormControl
			v-model="site"
			type="url"
			:label="__('Site address')"
			placeholder="https://yourname.m.frappe.cloud"
		/>
		<ErrorMessage :message="error" />
		<Button variant="solid" :loading="loading" :label="__('Link site')" @click="submit" />
	</div>
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
		await linkSite(site.value);
		emit("linked");
	} catch (e) {
		error.value = requestErrorMessage(e);
	} finally {
		loading.value = false;
	}
}
</script>
