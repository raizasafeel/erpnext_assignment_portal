<template>
	<Dialog
		v-model="open"
		:disable-outside-click-to-close="true"
		:options="dialogOptions"
	>
		<template #body-content>
			<div
				class="grid grid-cols-1 md:grid-cols-2 gap-y-2 text-p-base text-ink-gray-7"
			>
				<span class="font-medium text-ink-gray-9">Connected site</span>
				<span class="break-all">{{ siteUrl }}</span>
				<span class="font-medium text-ink-gray-9">Last checked</span>
				<span>{{ lastCheckedDisplay }}</span>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { Dialog, createResource, toast } from "frappe-ui"
import { computed, watch } from "vue"

const open = defineModel<boolean>({ required: true })

const props = defineProps<{
	siteUrl: string
	lastChecked: string | null
}>()

const emit = defineEmits<(e: "disconnected") => void>()

const disconnectSite = createResource({
	url: "erpnext_assignment_portal.erpnext_assignment_portal.api.disconnect_site",
})

const lastCheckedDisplay = computed(() => {
	if (!props.lastChecked) return "—"
	const d = new Date(props.lastChecked)
	return Number.isNaN(d.getTime()) ? props.lastChecked : d.toLocaleString()
})

const dialogOptions = computed(() => ({
	title: "Site details",
	actions: [
		{
			label: "Disconnect",
			variant: "solid" as const,
			loading: disconnectSite.loading,
			onClick: async ({ close }: { close: () => void }) => {
				try {
					await disconnectSite.submit()
					emit("disconnected")
					close()
				} catch (e: unknown) {
					const err = e as {
						messages: string[] | null
						message: string | null
					} | null
					toast.error(
						err?.messages?.[0] || err?.message || "Failed to disconnect",
					)
				}
			},
		},
	],
}))

watch(open, (v) => {
	if (v) disconnectSite.reset()
})
</script>
