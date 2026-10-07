(() => {
    "use strict";

    const page = document.querySelector("[data-profile-page]");
    if (!page) return;

    const panels = [...page.querySelectorAll("[data-profile-panel]")];
    const navigationLinks = [...page.querySelectorAll("[data-profile-nav] [data-profile-target]")];
    const allSectionLinks = [...page.querySelectorAll("[data-profile-target]")];
    const validSections = new Set(panels.map((panel) => panel.dataset.profilePanel));

    const normalizeSection = (value) => {
        const section = String(value || "").replace(/^#/, "");
        return validSections.has(section) ? section : (page.dataset.activeSection || "overview");
    };

    const activate = (section, { updateHistory = false, focus = false } = {}) => {
        const selected = normalizeSection(section);
        panels.forEach((panel) => {
            const active = panel.dataset.profilePanel === selected;
            panel.classList.toggle("is-active", active);
            panel.toggleAttribute("hidden", !active);
            if (active && focus) panel.focus({ preventScroll: true });
        });
        navigationLinks.forEach((link) => {
            const active = link.dataset.profileTarget === selected;
            link.classList.toggle("is-active", active);
            active ? link.setAttribute("aria-current", "page") : link.removeAttribute("aria-current");
        });
        page.dataset.activeSection = selected;
        if (updateHistory) history.replaceState(null, "", `#${selected}`);
    };

    allSectionLinks.forEach((link) => {
        link.addEventListener("click", (event) => {
            const selected = normalizeSection(link.dataset.profileTarget);
            event.preventDefault();
            activate(selected, { updateHistory: true, focus: true });
            page.querySelector(`[data-profile-panel="${selected}"]`)?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    });

    window.addEventListener("hashchange", () => activate(window.location.hash, { focus: true }));
    activate(window.location.hash || page.dataset.activeSection);

    page.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.dataset.confirm;
            if (message && !window.confirm(message)) event.preventDefault();
        });
    });

    const fallbackCopy = (value) => {
        const fallback = document.createElement("textarea");
        fallback.value = value;
        fallback.setAttribute("readonly", "");
        fallback.style.position = "fixed";
        fallback.style.opacity = "0";
        fallback.style.pointerEvents = "none";
        document.body.appendChild(fallback);
        fallback.select();
        const copied = document.execCommand("copy");
        fallback.remove();
        return copied;
    };

    const showCopyFeedback = (button) => {
        const label = button.querySelector("[data-copy-label]");
        const icon = button.querySelector("i");
        const successLabel = button.dataset.copySuccessLabel || "";
        if (!label || !successLabel) return;

        const originalLabel = label.textContent;
        const originalIconClass = icon?.className || "";
        label.textContent = successLabel;
        button.classList.add("is-copied");
        button.setAttribute("aria-live", "polite");
        if (icon) icon.className = "fa-solid fa-check";

        window.setTimeout(() => {
            label.textContent = originalLabel;
            button.classList.remove("is-copied");
            button.removeAttribute("aria-live");
            if (icon) icon.className = originalIconClass;
        }, 1400);
    };

    page.querySelectorAll("[data-copy-value]").forEach((button) => {
        button.addEventListener("click", async () => {
            const value = button.dataset.copyValue || "";
            if (!value || button.dataset.copyBusy === "1") return;

            button.dataset.copyBusy = "1";
            let copied = false;
            try {
                if (navigator.clipboard?.writeText) {
                    await navigator.clipboard.writeText(value);
                    copied = true;
                } else {
                    copied = fallbackCopy(value);
                }
            } catch (_error) {
                copied = fallbackCopy(value);
            } finally {
                delete button.dataset.copyBusy;
            }

            if (copied) showCopyFeedback(button);
        });
    });

    const photoInput = page.querySelector('input[type="file"][name="profile_photo"]');
    if (photoInput) {
        photoInput.addEventListener("change", () => {
            const [file] = photoInput.files || [];
            if (!file || !file.type.startsWith("image/")) return;
            const previewUrl = URL.createObjectURL(file);
            page.querySelectorAll("[data-profile-preview]").forEach((image) => {
                image.src = previewUrl;
                image.hidden = false;
            });
            page.querySelectorAll("[data-profile-fallback]").forEach((fallback) => { fallback.hidden = true; });
        });
    }
})();
