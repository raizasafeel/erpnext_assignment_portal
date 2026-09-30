<template>
	<section
		class="flex flex-col gap-5 rounded-7 border border-outline-gray-2 bg-surface-base p-5 sm:p-6"
	>
		<div class="flex flex-wrap items-start justify-between gap-4">
			<div class="flex min-w-0 max-w-2xl flex-col gap-1.5">
				<h1 class="text-xl font-semibold text-ink-gray-9">
					{{ __("Hi {0}, here's how your ERPNext site is doing", [firstName]) }}
				</h1>
				<p class="text-p-base text-ink-gray-7">
					{{ __("We automatically check your practice site against each assignment.") }}
					<span class="font-medium text-ink-green-7">{{ __("Green means done.") }}</span>
					<span class="font-medium text-ink-red-6">{{
						__("Red means it still needs work.")
					}}</span>
					{{ __("Fix the red items below, then press Re-check.") }}
				</p>
			</div>
			<Button
				variant="solid"
				icon-left="lucide-refresh-cw"
				:loading="grading"
				:disabled="blocked"
				:label="__('Re-check site')"
				@click="emit('recheck')"
			/>
		</div>
		<div
			class="grid gap-4 border-t border-outline-gray-1 pt-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]"
		>
			<div class="flex items-center gap-4">
				<ProgressRing :value="overview.percent" />
				<div class="flex flex-col gap-1">
					<p class="text-base font-semibold text-ink-gray-9">{{ encouragement }}</p>
					<p class="text-sm text-ink-gray-5">
						{{ __("{0} of {1} checks passing", [overview.passed, overview.total]) }}
					</p>
				</div>
			</div>
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
				<div
					v-for="stat in stats"
					:key="stat.key"
					:data-stat="stat.key"
					class="flex flex-col gap-1 rounded-6 border border-outline-gray-2 p-3"
				>
					<span class="size-5" :class="stat.icon" aria-hidden="true" />
					<span class="text-2xl font-semibold" :class="stat.tone">{{ stat.value }}</span>
					<span class="text-sm text-ink-gray-5">{{ stat.label }}</span>
				</div>
			</div>
		</div>
	</section>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import { computed } from "vue";
import type { Overview } from "../lib/scores";
import { __ } from "../translate";
import ProgressRing from "./ProgressRing.vue";

const props = defineProps<{
	fullName: string;
	overview: Overview;
	grading: boolean;
	blocked: boolean;
}>();
const emit = defineEmits<{ recheck: [] }>();

const firstName = computed(() => props.fullName.trim().split(/\s+/)[0] || __("there"));

const encouragement = computed(() => {
	const { percent, total, passed } = props.overview;
	if (total && passed === total) return __("All done. Every check is passing.");
	if (percent >= 75) return __("Almost there. Only a few red items are left.");
	if (percent >= 25) return __("Good progress. Keep working through the red items.");
	return __("Let's get started. Work through the sections below.");
});

const stats = computed(() => [
	{
		key: "passed",
		value: String(props.overview.passed),
		label: __("Checks passed"),
		icon: "lucide-circle-check text-ink-green-6",
		tone: "text-ink-green-7",
	},
	{
		key: "to-fix",
		value: String(props.overview.total - props.overview.passed),
		label: __("Still to fix"),
		icon: "lucide-circle-alert text-ink-red-6",
		tone: "text-ink-red-6",
	},
	{
		key: "sections",
		value: `${props.overview.sectionsDone}/${props.overview.sectionsTotal}`,
		label: __("Sections done"),
		icon: "lucide-list-checks text-ink-gray-6",
		tone: "text-ink-gray-9",
	},
]);
</script>
