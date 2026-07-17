(() => {
    "use strict";

    const RevealSelectorVO = Object.freeze({
        all: ".reveal, .reveal_right, .reveal_left",
        activeClass: "activee",
        readyClass: "reveal-ready",
        pendingClass: "reveal-pending",
    });

    const revealImmediately = (targets) => {
        targets.forEach((target) => target.classList.add(RevealSelectorVO.activeClass));
    };

    const initHeroTitle = () => {
        const heroTitle = document.querySelector("#hero_title");
        heroTitle?.classList.add("is-ready");
    };

    const initReveals = () => {
        const root = document.documentElement;
        const targets = [...document.querySelectorAll(RevealSelectorVO.all)];

        root.classList.add(RevealSelectorVO.readyClass);
        root.classList.remove(RevealSelectorVO.pendingClass);

        if (!targets.length) {
            return;
        }

        const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
        if (!("IntersectionObserver" in window) || reducedMotion) {
            revealImmediately(targets);
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) {
                        return;
                    }

                    entry.target.classList.add(RevealSelectorVO.activeClass);
                    observer.unobserve(entry.target);
                });
            },
            {
                threshold: 0.08,
                rootMargin: "0px 0px -2% 0px",
            },
        );

        targets.forEach((target) => observer.observe(target));
    };

    const initializeEffects = () => {
        initHeroTitle();
        initReveals();
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeEffects, {once: true});
    } else {
        initializeEffects();
    }
})();
