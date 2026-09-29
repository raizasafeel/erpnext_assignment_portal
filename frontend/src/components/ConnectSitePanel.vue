<template>
	<div
		class="align-middle mx-auto max-w-lg w-full rounded-2xl border border-outline-gray-2 bg-surface-white p-8"
	>
		<div class="mb-6 flex flex-col items-center gap-3 text-center">
			<GraderLogo />
			<div>
				<h1 class="text-xl font-semibold tracking-tight text-ink-gray-9">
					ERPNext Assignment Portal
				</h1>
				<p class="mt-1 text-sm text-ink-gray-5">
					Paste your practice-site URL to start grading
				</p>
			</div>
		</div>

		<form class="flex flex-col gap-4" @submit.prevent="submit">
			<FormControl
				v-model="siteInput"
				type="text"
				label="Practice site URL"
				placeholder="https://your-site.localhost"
				:readonly="!!defaultSite"
			/>
			<Button
				variant="solid"
				theme="gray"
				:loading="registerSite.loading"
				type="submit"
				class="w-full"
			>
				Connect site
			</Button>
			<p v-if="defaultSite" class="text-center text-xs text-ink-gray-5">
				To connect a different site, contact
				<a href="mailto:school@frappe.io" class="text-ink-blue-3 hover:underline"
					>school@frappe.io</a
				>.
			</p>
			<ErrorMessage
				v-if="registerSite.error"
				:message="registerSite.error.messages?.[0] || 'Failed to connect'"
			/>
		</form>
	</div>
</template>

<script setup lang="ts">
import { Button, ErrorMessage, FormControl, createResource } from "frappe-ui";
import { ref, watch } from "vue";
import GraderLogo from "./GraderLogo.vue";

const props = defineProps<{
	defaultSite: string;
}>();

const emit = defineEmits<(e: "connected") => void>();

const registerSite = createResource({
	url: "erpnext_assignment_portal.erpnext_assignment_portal.api.register_site",
});

const siteInput = ref("");
watch(
	() => props.defaultSite,
	(v) => {
		if (v && !siteInput.value) siteInput.value = v;
	},
	{ immediate: true },
);

async function submit() {
	const url = siteInput.value.trim();
	if (!url) return;
	// Belt-and-suspenders: the input is readonly when defaultSite is set,
	// but if it ever gets bypassed we still don't submit a mismatched URL —
	// the backend rejects this case with a "contact support" error.
	if (props.defaultSite && url !== props.defaultSite.trim()) return;
	await registerSite.submit({ site: url });
	emit("connected");
}
</script>
