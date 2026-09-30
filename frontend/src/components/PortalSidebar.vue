<template>
	<Sidebar :collapsible="false" width="17rem" :aria-label="__('Sections')">
		<div class="p-2">
			<Dropdown :options="menu" match-trigger-width>
				<template #default="{ open }">
					<button
						type="button"
						class="flex min-h-12 w-full items-center gap-2 rounded-3 px-2 py-1 text-start"
						:class="
							open ? 'bg-surface-elevation-2 shadow-sm' : 'hover:bg-surface-gray-3'
						"
					>
						<img :src="LOGO" alt="" class="size-7 shrink-0 rounded-3" />
						<span class="flex min-w-0 flex-1 flex-col">
							<span class="truncate text-p-base-medium text-ink-gray-8">
								{{ __("ERPNext Assignment Portal") }}
							</span>
							<span class="truncate text-p-sm text-ink-gray-6">{{ fullName }}</span>
						</span>
						<span
							class="lucide-chevron-down size-4 shrink-0 text-ink-gray-7"
							aria-hidden="true"
						/>
					</button>
				</template>
			</Dropdown>
		</div>
		<div class="px-2 pb-2">
			<TextInput
				v-model="filter"
				class="[&_input]:text-p-base"
				:aria-label="__('Filter sections')"
				type="search"
				:placeholder="__('Filter sections')"
			>
				<template #prefix>
					<span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
				</template>
			</TextInput>
		</div>
		<ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pb-6">
			<SidebarLabel>
				<span class="text-p-base">{{ __("Sections") }}</span>
			</SidebarLabel>
			<div class="mt-0.5 flex flex-col gap-0.5">
				<SidebarItem
					v-for="s in visible"
					:key="s.slug"
					:label="s.title"
					:active="s.slug === active"
					:aria-label="itemLabel(s)"
					:data-status="sectionStatus(scores[s.slug])"
					@click="emit('pick', s.slug)"
				>
					<span class="truncate text-p-sm">{{ s.title }}</span>
					<template #suffix>
						<span class="me-2 text-p-sm text-ink-gray-4">
							{{ scores[s.slug].passed }}/{{ scores[s.slug].total }}
						</span>
					</template>
					<template #prefix>
						<span
							class="size-2 rounded-full"
							:class="DOT[sectionStatus(scores[s.slug])]"
						/>
					</template>
				</SidebarItem>
				<p v-if="!visible.length" class="px-2 py-1 text-p-sm text-ink-gray-5">
					{{ __("No matching sections") }}
				</p>
			</div>
		</ScrollArea>
	</Sidebar>
</template>

<script setup lang="ts">
import {
	Dropdown,
	type DropdownOptions,
	ScrollArea,
	Sidebar,
	SidebarItem,
	SidebarLabel,
	TextInput,
} from "frappe-ui";
import { computed, ref } from "vue";
import type { Section } from "../api";
import { type Score, type SectionStatus, sectionStatus } from "../lib/scores";
import { __ } from "../translate";

const LOGO = "/assets/erpnext_assignment_portal/images/portal-logo.svg";
const DOT: Record<SectionStatus, string> = {
	done: "bg-surface-green-7",
	partial: "bg-surface-amber-6",
	todo: "bg-surface-red-4",
};

const props = defineProps<{
	sections: Section[];
	scores: Record<string, Score>;
	active?: string;
	fullName: string;
	menu: DropdownOptions;
}>();
const emit = defineEmits<{ pick: [slug: string] }>();

const STATUS_TEXT: Record<SectionStatus, string> = {
	done: __("Done"),
	partial: __("In progress"),
	todo: __("Not started"),
};

const filter = ref("");

function itemLabel(s: Section) {
	const score = props.scores[s.slug];
	return __("{0}, {1}, {2} of {3} checks passing", [
		s.title,
		STATUS_TEXT[sectionStatus(score)],
		score.passed,
		score.total,
	]);
}
const visible = computed(() => {
	const q = filter.value.trim().toLowerCase();
	return q ? props.sections.filter((s) => s.title.toLowerCase().includes(q)) : props.sections;
});
</script>
