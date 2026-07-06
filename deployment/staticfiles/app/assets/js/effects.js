(() => {
    'use strict';

    const heroTitle = document.querySelector('#hero_title');
    const text = ' مسیر حرفه‌ای یادگیری برنامه‌نویسی؛ از اولین خط کد تا استخدام';
    let index = 0;

    function typeText() {
        if (!heroTitle) return;
        if (index < text.length) {
            heroTitle.textContent += text.charAt(index);
            index += 1;
            window.setTimeout(typeText, 52);
        }
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
        typeText();
        initReveals();
    });
})();
