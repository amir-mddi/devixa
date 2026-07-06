(() => {
    'use strict';

    function initHeroTitle() {
        const heroTitle = document.querySelector('#hero_title');
        if (!heroTitle) return;

        // Keep the hero heading stable. The old typewriter appended a long
        // second sentence to the title, which made Persian text break into
        // too many oversized lines on laptop screens.
        heroTitle.classList.add('is-ready');
    }

    function initReveals() {
        const revealTargets = document.querySelectorAll('.reveal, .reveal_right, .reveal_left');
        if (!revealTargets.length) return;

        if (!('IntersectionObserver' in window)) {
            revealTargets.forEach((item) => item.classList.add('activee'));
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('activee');
                } else {
                    entry.target.classList.remove('activee');
                }
            });
        }, { threshold: 0.15, rootMargin: '0px 0px -4% 0px' });

        revealTargets.forEach((item) => observer.observe(item));
    }

    window.addEventListener('DOMContentLoaded', () => {
        initHeroTitle();
        initReveals();
    });
})();
