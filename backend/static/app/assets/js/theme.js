(() => {
    "use strict";
    const toggle = document.getElementById("theme_toggle");
    if (!toggle) return;

    // The synchronous head bootstrap already applied the saved theme before paint.
    window.DevixaTheme?.syncBody();
    toggle.addEventListener("change", () => {
        window.DevixaTheme?.apply(toggle.checked ? "light" : "dark", true);
    });
})();
