<template>
	<Sidebar :collapsible="false" width="17rem" :aria-label="__('Sections')">
		<div class="px-1 pt-2">
			<SidebarHeader
				:title="__('ERPNext Assignment Portal')"
				:subtitle="fullName"
				:logo="LOGO"
				:menu-items="menu"
			/>
		</div>
		<div class="px-2 pb-2 pt-1">
			<TextInput v-model="filter" type="search" :placeholder="__('Filter sections')">
				<template #prefix>
					<span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
				</template>
			</TextInput>
		</div>
		<ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pb-6">
			<SidebarLabel>{{ __("Sections") }}</SidebarLabel>
			<div class="mt-0.5 flex flex-col gap-0.5">
				<SidebarItem
					v-for="s in visible"
					:key="s.slug"
					:label="s.title"
					:suffix="`${scores[s.slug].passed}/${scores[s.slug].total}`"
					:active="s.slug === active"
					:data-status="sectionStatus(scores[s.slug])"
					@click="emit('pick', s.slug)"
				>
					<template #prefix>
						<span
							class="size-2 rounded-full"
							:class="DOT[sectionStatus(scores[s.slug])]"
						/>
					</template>
				</SidebarItem>
				<p v-if="!visible.length" class="px-2 py-1 text-sm text-ink-gray-5">
					{{ __("No matching sections") }}
				</p>
			</div>
		</ScrollArea>
	</Sidebar>
</template>

<script setup lang="ts">
import {
	type DropdownOptions,
	ScrollArea,
	Sidebar,
	SidebarHeader,
	SidebarItem,
	SidebarLabel,
	TextInput,
} from "frappe-ui";
import { computed, ref } from "vue";
import type { Section } from "../api";
import { type Score, type SectionStatus, sectionStatus } from "../lib/scores";

const LOGO = "/assets/erpnext_assignment_portal/images/logo.svg";
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

const filter = ref("");
const visible = computed(() => {
	const q = filter.value.trim().toLowerCase();
	return q ? props.sections.filter((s) => s.title.toLowerCase().includes(q)) : props.sections;
});
</script>
