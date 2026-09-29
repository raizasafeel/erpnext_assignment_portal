<template>
	<Alert
		v-if="revoked"
		theme="red"
		:title="__('Your site access was revoked')"
		:description="__('Contact the course staff to restore it.')"
	/>
	<Alert
		v-else-if="expired"
		theme="amber"
		:title="__('Your site link has expired')"
		:description="__('Ask your instructor to extend it.')"
	/>
	<Alert
		v-else-if="run?.status === 'Error'"
		theme="red"
		:title="__('Grading failed')"
		:description="runErrorMessage(run.error_code)"
	/>
	<Alert
		v-else-if="stillRunning"
		theme="blue"
		:title="__('Still grading')"
		:description="__('We will update this page when it finishes.')"
	/>
</template>

<script setup lang="ts">
import { Alert } from "frappe-ui";
import type { Run } from "../api";
import { runErrorMessage } from "../lib/errors";

defineProps<{ run: Run | null; expired: boolean; revoked: boolean; stillRunning: boolean }>();
</script>
