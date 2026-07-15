(() => {
    "use strict";

    const navMenu = document.getElementById("navmenu");
    const menuButton = document.querySelector("[data-menu-toggle]");
    const desktopQuery = window.matchMedia("(min-width: 981px)");
    const accountMenus = Array.from(document.querySelectorAll(".auth-menu"));

    const setMenuState = (isOpen) => {
        if (!navMenu) return;
        navMenu.classList.toggle("responsive", isOpen);
        menuButton?.setAttribute("aria-expanded", String(isOpen));
        document.body.classList.toggle("mobile-menu-open", isOpen);
    };

    const closeAccountMenus = (exceptMenu = null) => {
        accountMenus.forEach((menu) => {
            if (menu === exceptMenu) return;
            menu.classList.remove("is-open");
            menu.querySelector(".auth-menu__trigger")?.setAttribute("aria-expanded", "false");
        });
    };

    menuButton?.addEventListener("click", () => {
        closeAccountMenus();
        setMenuState(!navMenu?.classList.contains("responsive"));
    });

    navMenu?.addEventListener("click", (event) => {
        if (event.target.closest("a")) setMenuState(false);
    });

    accountMenus.forEach((menu) => {
        const trigger = menu.querySelector(".auth-menu__trigger");
        if (!trigger) return;

        trigger.setAttribute("aria-expanded", "false");
        trigger.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            const shouldOpen = !menu.classList.contains("is-open");
            closeAccountMenus(menu);
            menu.classList.toggle("is-open", shouldOpen);
            trigger.setAttribute("aria-expanded", String(shouldOpen));
            setMenuState(false);
        });
    });

    document.addEventListener("click", (event) => {
        if (
            navMenu?.classList.contains("responsive") &&
            !event.target.closest("#navmenu") &&
            !event.target.closest("[data-menu-toggle]")
        ) {
            setMenuState(false);
        }
        if (!event.target.closest(".auth-menu")) closeAccountMenus();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        setMenuState(false);
        closeAccountMenus();
    });

    desktopQuery.addEventListener("change", (event) => {
        if (event.matches) setMenuState(false);
        closeAccountMenus();
    });

    document.querySelectorAll("[data-confirm-message]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.dataset.confirmMessage?.trim();
            if (message && !window.confirm(message)) event.preventDefault();
        });
    });

    document.querySelectorAll("[data-auto-submit]").forEach((control) => {
        control.addEventListener("change", () => control.form?.requestSubmit());
    });

    const fitTextElements = Array.from(document.querySelectorAll("[data-fit-text]"));

    const fitElementText = (element) => {
        const label = element.querySelector("[data-fit-text-label]");
        if (!label || element.clientWidth <= 0) return;

        const elementStyle = window.getComputedStyle(element);
        const labelStyle = window.getComputedStyle(label);
        const icon = element.querySelector(":scope > i, :scope > svg");
        const iconWidth = icon?.getBoundingClientRect().width || 0;
        const gap = icon ? Number.parseFloat(elementStyle.columnGap || elementStyle.gap || "0") || 0 : 0;
        const horizontalPadding =
            (Number.parseFloat(elementStyle.paddingInlineStart) || 0) +
            (Number.parseFloat(elementStyle.paddingInlineEnd) || 0);
        const maximumFontSize =
            Number.parseFloat(element.dataset.fitTextMax || label.dataset.fitTextMax) ||
            Number.parseFloat(labelStyle.fontSize) ||
            13;
        const minimumFontSize =
            Number.parseFloat(element.dataset.fitTextMin || label.dataset.fitTextMin) || 9;
        const availableWidth = Math.max(
            1,
            element.clientWidth - horizontalPadding - iconWidth - gap,
        );

        label.style.fontSize = `${maximumFontSize}px`;
        if (label.scrollWidth <= availableWidth) return;

        const fittedSize = Math.max(
            minimumFontSize,
            maximumFontSize * (availableWidth / label.scrollWidth),
        );
        label.style.fontSize = `${Math.floor(fittedSize * 10) / 10}px`;
    };

    const fitAllTextElements = () => fitTextElements.forEach(fitElementText);

    if (fitTextElements.length) {
        window.requestAnimationFrame(fitAllTextElements);
        document.fonts?.ready.then(fitAllTextElements);

        if ("ResizeObserver" in window) {
            const observer = new ResizeObserver((entries) => {
                entries.forEach(({target}) => fitElementText(target));
            });
            fitTextElements.forEach((element) => observer.observe(element));
        } else {
            window.addEventListener("resize", fitAllTextElements, {passive: true});
        }
    }

    const activeKeyFor = (pathname) => {
        const path = String(pathname || "/").replace(/\/{2,}/g, "/");
        if (path === "/" || path === "") return "home";
        if (/^\/courses(?:\/|$)/.test(path)) return "courses";
        if (/^\/roadmaps(?:\/|$)/.test(path)) return "roadmaps";
        if (/^\/channels(?:\/|$)/.test(path)) return "channels";
        if (/^\/contact-us(?:\/|$)/.test(path)) return "contact";
        if (/^\/(?:articles|blog|news)(?:\/|$)/.test(path)) return "articles";
        return "";
    };

    const activeKey = activeKeyFor(window.location.pathname);
    document.querySelectorAll("[data-mobile-nav-link]").forEach((link) => {
        const isActive = Boolean(activeKey) && link.dataset.mobileNavLink === activeKey;
        link.classList.toggle("is-active", isActive);
        if (isActive) link.setAttribute("aria-current", "page");
        else link.removeAttribute("aria-current");
    });

    const flashStacks = document.querySelectorAll("[data-project-global-flash]");
    if (flashStacks.length) {
        window.setTimeout(() => {
            flashStacks.forEach((stack) => {
                stack.classList.add("project-global-flash--is-hiding");
                window.setTimeout(() => stack.remove(), 450);
            });
        }, 3000);
    }
})();
