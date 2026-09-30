import { type ColorScheme, useColorScheme } from "frappe-ui"

export function useTheme() {
	let scheme: ReturnType<typeof useColorScheme>
	try {
		scheme = useColorScheme()
	} catch {
		// localStorage can throw (private mode, blocked storage); the singleton is initialised by then.
		scheme = useColorScheme()
	}
	return {
		colorScheme: scheme.colorScheme,
		setColorScheme(value: ColorScheme) {
			try {
				scheme.setColorScheme(value)
			} catch {
				// data-theme is applied before the storage write that threw.
			}
		},
	}
}
