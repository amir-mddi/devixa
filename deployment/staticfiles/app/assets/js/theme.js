(() => {
    "use strict";

    const ThemeVO = Object.freeze({
        storageKey: "theme",
        light: "light",
        dark: "dark",
    });

    const menubar = document.getElementById("menubar");
    const toggle = document.getElementById("theme_toggle");
    if (!toggle) {
        return;
    }

    const readStoredTheme = () => {
        try {
            return window.localStorage.getItem(ThemeVO.storageKey);
        } catch (error) {
            return null;
        }
    };

    const storeTheme = (themeName) => {
        try {
            window.localStorage.setItem(ThemeVO.storageKey, themeName);
        } catch (error) {
            // Storage can be unavailable in strict privacy or embedded contexts.
        }
    };

    const savedTheme = readStoredTheme();
    const prefersLight = window.matchMedia?.("(prefers-color-scheme: light)")?.matches ?? false;
    const shouldUseLight = savedTheme ? savedTheme === ThemeVO.light : prefersLight;

    const applyTheme = (isLight) => {
        const themeName = isLight ? ThemeVO.light : ThemeVO.dark;
        document.body.classList.toggle("light-theme", isLight);
        document.body.dataset.theme = themeName;
        document.documentElement.dataset.theme = themeName;
        document.documentElement.style.colorScheme = themeName;
        toggle.checked = isLight;
        menubar?.classList.toggle("background", isLight);
        storeTheme(themeName);

        document
            .querySelector('meta[name="theme-color"]')
            ?.setAttribute("content", isLight ? "#f5f7ff" : "#070b14");
    };

    applyTheme(shouldUseLight);
    toggle.addEventListener("change", () => applyTheme(toggle.checked));
})();
