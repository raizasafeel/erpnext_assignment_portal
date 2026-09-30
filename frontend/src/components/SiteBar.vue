<template>
	<div class="flex min-w-0 flex-wrap items-center gap-x-4 gap-y-2">
		<Popover align="start">
			<template #trigger>
				<Button variant="outline" :label="host" :aria-label="__('Site details')">
					<template #prefix>
						<span
							class="size-2 shrink-0 rounded-full"
							:class="blocked ? 'bg-surface-red-6' : 'bg-surface-green-7'"
						/>
					</template>
				</Button>
			</template>
			<template #default="{ close }">
				<dl class="flex w-72 flex-col gap-2 p-3 text-sm">
					<div class="flex justify-between gap-4">
						<dt class="text-ink-gray-5">{{ __("Site") }}</dt>
						<dd class="truncate text-ink-gray-8">{{ host }}</dd>
					</div>
					<div class="flex justify-between gap-4">
						<dt class="text-ink-gray-5">{{ __("Status") }}</dt>
						<dd class="text-ink-gray-8">{{ statusLabel }}</dd>
					</div>
					<div v-if="site.expires_on" class="flex justify-between gap-4">
						<dt class="text-ink-gray-5">{{ __("Link expires") }}</dt>
						<dd class="text-ink-gray-8">{{ site.expires_on }}</dd>
					</div>
					<Button
						class="mt-1"
						icon-left="lucide-link"
						:label="__('Link a different site')"
						@click="close(), emit('relink')"
					/>
				</dl>
			</template>
		</Popover>
		<span v-if="checkedOn" class="flex items-center gap-1.5 text-sm text-ink-gray-5">
			<span class="lucide-clock size-4" aria-hidden="true" />
			{{ __("Checked {0}", [checkedOn]) }}
		</span>
		<div class="flex w-40 flex-col gap-1">
			<div class="flex justify-between text-sm">
				<span class="text-ink-gray-5">{{ __("Overall progress") }}</span>
				<span class="text-ink-gray-8"
					>{{ overview.sectionsDone }}/{{ overview.sectionsTotal }}</span
				>
			</div>
			<Progress :value="sectionsPercent" size="sm" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { Button, Popover, Progress } from "frappe-ui";
import { computed } from "vue";
import type { Context, Run } from "../api";
import type { Overview } from "../lib/scores";
import { __ } from "../translate";

const props = defineProps<{
	site: NonNullable<Context["site"]>;
	run: Run | null;
	overview: Overview;
}>();
const emit = defineEmits<{ relink: [] }>();

const host = computed(() => props.site.site.replace(/^https?:\/\//, ""));
const blocked = computed(() => props.site.expired || props.site.revoked);
const checkedOn = computed(() => props.run?.finished_on?.slice(0, 16) ?? "");
const sectionsPercent = computed(() =>
	props.overview.sectionsTotal
		? Math.round((props.overview.sectionsDone / props.overview.sectionsTotal) * 100)
		: 0
);
const statusLabel = computed(() => {
	if (props.site.revoked) return __("Revoked");
	if (props.site.expired) return __("Expired");
	return props.site.status === "Active" ? __("Active") : __("Inactive");
});
</script>
