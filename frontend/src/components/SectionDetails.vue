<template>
	<Editor :model-value="html" :editable="false" :extensions="[RichTextKit]">
		<EditorContent />
	</Editor>
</template>

<script setup lang="ts">
import { Editor, EditorContent, RichTextKit } from "frappe-ui/editor";

defineProps<{ html: string }>();
</script>
