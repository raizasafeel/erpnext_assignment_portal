<template>
	<div class="flex min-h-screen items-center justify-center bg-surface-gray-1 px-4 py-10">
		<div
			class="flex w-full max-w-lg flex-col gap-7 rounded-7 border border-outline-gray-2 bg-surface-base px-6 py-8 sm:px-9 sm:py-10"
		>
			<div class="flex flex-col items-center gap-3 text-center">
				<img :src="LOGO" alt="" class="size-12 rounded-4" />
				<h1 class="text-xl font-semibold text-ink-gray-9">
					{{ __("Connect your practice site") }}
				</h1>
				<p class="text-p-base text-ink-gray-6">
					{{
						__(
							"We check your ERPNext trial against each assignment. Connect it once to get started."
						)
					}}
				</p>
			</div>
			<ol class="flex flex-col gap-3">
				<li v-for="(step, i) in steps" :key="i" class="flex items-start gap-3">
					<span
						class="flex size-6 shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-sm font-medium text-ink-gray-7"
						>{{ i + 1 }}</span
					>
					<span class="pt-0.5 text-p-base text-ink-gray-7">{{ step }}</span>
				</li>
			</ol>
			<LinkSiteForm @linked="emit('linked')" />
			<div class="flex justify-center border-t border-outline-gray-1 pt-5">
				<Button
					variant="ghost"
					icon-left="lucide-log-out"
					:label="__('Log out')"
					@click="emit('logout')"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import { __ } from "../translate";
import LinkSiteForm from "./LinkSiteForm.vue";

const emit = defineEmits<{ linked: []; logout: [] }>();

const LOGO = "/assets/erpnext_assignment_portal/images/portal-logo.svg";
const steps = [
	__("Start an ERPNext trial on Frappe Cloud with the same email you use here."),
	__("Install the ERPNext Assignment Checks app on that site."),
	__("Paste the site address below and connect."),
];
</script>
