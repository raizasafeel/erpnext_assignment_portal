<template>
	<div class="flex min-h-screen items-center justify-center bg-surface-gray-1 px-4 py-10">
		<div
			class="flex w-full max-w-md flex-col items-center gap-6 rounded-7 border border-outline-gray-2 bg-surface-base px-6 py-10 text-center sm:px-10"
		>
			<div class="flex size-14 items-center justify-center rounded-full bg-surface-amber-2">
				<span class="lucide-graduation-cap size-7 text-ink-amber-3" aria-hidden="true" />
			</div>
			<div class="flex flex-col gap-2">
				<h1 class="text-xl font-semibold text-ink-gray-9">
					{{ __("You're not enrolled yet") }}
				</h1>
				<p class="text-p-base text-ink-gray-6">
					{{
						course
							? __(
									"This checker is for students of {0}. Enroll in the course and come back to check your site.",
									[course.title]
							  )
							: __(
									"This checker is for enrolled students. Enroll in the course and come back to check your site."
							  )
					}}
				</p>
			</div>
			<div class="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
				<Button
					v-if="course"
					variant="solid"
					icon-left="lucide-book-open"
					:label="__('Go to the course')"
					:href="`/lms/courses/${course.name}`"
				/>
				<Button
					variant="subtle"
					icon-left="lucide-log-out"
					:label="__('Log out')"
					@click="emit('logout')"
				/>
			</div>
			<p class="text-p-sm text-ink-gray-5">{{ __("Signed in as {0}", [user]) }}</p>
		</div>
	</div>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import { __ } from "../translate";

defineProps<{ course: { name: string; title: string } | null; user: string }>();
const emit = defineEmits<{ logout: [] }>();
</script>
