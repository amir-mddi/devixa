(() => {
    'use strict';

    const navMenu = document.getElementById('navmenu');
    const menuButton = document.querySelector('.navbar .bars');
    const desktopQuery = window.matchMedia('(min-width: 981px)');
    const accountMenus = [...document.querySelectorAll('.auth-menu')];

    function setMenuState(isOpen) {
        if (!navMenu) return;
        navMenu.classList.toggle('responsive', isOpen);
        if (menuButton) menuButton.setAttribute('aria-expanded', String(isOpen));
        document.body.classList.toggle('mobile-menu-open', isOpen);
    }

    function closeAccountMenus(exceptMenu = null) {
        accountMenus.forEach((menu) => {
            if (menu !== exceptMenu) {
                menu.classList.remove('is-open');
                const trigger = menu.querySelector('.auth-menu__trigger');
                if (trigger) trigger.setAttribute('aria-expanded', 'false');
            }
        });
    }

    window.respo = function respo() {
        if (!navMenu) return;
        closeAccountMenus();
        setMenuState(!navMenu.classList.contains('responsive'));
    };

    if (menuButton) {
        menuButton.setAttribute('aria-expanded', 'false');
    }

    if (navMenu) {
        navMenu.addEventListener('click', (event) => {
            if (event.target.closest('a')) setMenuState(false);
        });
    }

    accountMenus.forEach((menu) => {
        const trigger = menu.querySelector('.auth-menu__trigger');
        if (!trigger) return;

        trigger.setAttribute('aria-expanded', 'false');
        trigger.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            const isOpen = menu.classList.contains('is-open');
            closeAccountMenus(menu);
            menu.classList.toggle('is-open', !isOpen);
            trigger.setAttribute('aria-expanded', String(!isOpen));
            setMenuState(false);
        });
    });

    document.addEventListener('click', (event) => {
        if (navMenu && navMenu.classList.contains('responsive')) {
            const isMenuClick = event.target.closest('#navmenu');
            const isBarsClick = event.target.closest('.bars');
            if (!isMenuClick && !isBarsClick) setMenuState(false);
        }

        if (!event.target.closest('.auth-menu')) closeAccountMenus();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            setMenuState(false);
            closeAccountMenus();
        }
    });

    desktopQuery.addEventListener('change', (event) => {
        if (event.matches) setMenuState(false);
    });

    window.addEventListener('resize', () => {
        if (desktopQuery.matches) setMenuState(false);
        closeAccountMenus();
    }, { passive: true });

    const track = document.querySelector('.testimonial_track');
    const cards = track ? [...track.querySelectorAll('.testimonial_card')] : [];
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    let currentIndex = 0;

    if (track && cards.length && prevBtn && nextBtn) {
        function getVisibleCount() {
            const width = track.parentElement.offsetWidth;
            if (width >= 1024) return 3;
            if (width >= 640) return 2;
            return 1;
        }

        function getGap() {
            return parseFloat(getComputedStyle(track).gap || '24') || 24;
        }

        function updateCardWidths() {
            const visibleCount = getVisibleCount();
            const gap = getGap();
            const totalGaps = (visibleCount - 1) * gap;
            const cardWidth = Math.max(0, (track.parentElement.offsetWidth - totalGaps) / visibleCount);
            cards.forEach((card) => {
                card.style.width = `${cardWidth}px`;
            });
        }

        function getCardWidth() {
            return (cards[0]?.offsetWidth || 0) + getGap();
        }

        function updateSlider() {
            track.style.transform = `translateX(${currentIndex * getCardWidth() * -1}px)`;
        }

        function getMaxIndex() {
            return -(cards.length - getVisibleCount());
        }

        nextBtn.addEventListener('click', (event) => {
            event.preventDefault();
            if (currentIndex > getMaxIndex()) {
                currentIndex -= 1;
                updateSlider();
            }
        });

        prevBtn.addEventListener('click', (event) => {
            event.preventDefault();
            if (currentIndex < 0) {
                currentIndex += 1;
                updateSlider();
            }
        });

        window.addEventListener('resize', () => {
            currentIndex = 0;
            updateCardWidths();
            updateSlider();
        }, { passive: true });

        updateCardWidths();
        updateSlider();
    }

    const firstChip = document.querySelector('.courses_section .courses_hero .category_chips .chip a');
    if (firstChip) firstChip.addEventListener('click', (event) => event.preventDefault());
})();
