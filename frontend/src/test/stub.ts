import { defineComponent, h } from "vue"

export function stub(name: string) {
	return defineComponent({
		name,
		inheritAttrs: false,
		setup(_, { attrs, slots }) {
			return () =>
				h(
					"div",
					{ "data-stub": name, "data-title": attrs.title },
					Object.values(slots).map((slot) => slot?.()),
				)
		},
	})
}
