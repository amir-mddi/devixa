(() => {
    "use strict";

    let savedTheme = null;
    try {
        savedTheme = window.localStorage.getItem("theme");
    } catch (error) {
        savedTheme = null;
    }

    const prefersLight = window.matchMedia?.("(prefers-color-scheme: light)").matches ?? false;
    const theme = savedTheme || (prefersLight ? "light" : "dark");
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
})();
