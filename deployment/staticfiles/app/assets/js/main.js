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

    const fitTextElements = [...document.querySelectorAll('[data-fit-text]')];

    function fitElementText(element) {
        const label = element.querySelector('[data-fit-text-label]');
        if (!label || element.clientWidth <= 0) return;

        const elementStyle = window.getComputedStyle(element);
        const labelStyle = window.getComputedStyle(label);
        const icon = element.querySelector(':scope > i, :scope > svg');
        const iconWidth = icon ? icon.getBoundingClientRect().width : 0;
        const gap = icon
            ? parseFloat(elementStyle.columnGap || elementStyle.gap || '0') || 0
            : 0;
        const horizontalPadding =
            (parseFloat(elementStyle.paddingInlineStart) || 0) +
            (parseFloat(elementStyle.paddingInlineEnd) || 0);
        const maximumFontSize =
            parseFloat(element.dataset.fitTextMax || label.dataset.fitTextMax) ||
            parseFloat(labelStyle.fontSize) ||
            13;
        const minimumFontSize =
            parseFloat(element.dataset.fitTextMin || label.dataset.fitTextMin) || 9;
        const availableWidth = Math.max(
            1,
            element.clientWidth - horizontalPadding - iconWidth - gap,
        );

        label.style.fontSize = `${maximumFontSize}px`;
        const requiredWidth = label.scrollWidth;

        if (requiredWidth <= availableWidth) return;

        const fittedSize = Math.max(
            minimumFontSize,
            maximumFontSize * (availableWidth / requiredWidth),
        );

        label.style.fontSize = `${Math.floor(fittedSize * 10) / 10}px`;
    }

    function fitAllTextElements() {
        fitTextElements.forEach(fitElementText);
    }

    if (fitTextElements.length) {
        requestAnimationFrame(fitAllTextElements);

        if (document.fonts?.ready) {
            document.fonts.ready.then(fitAllTextElements);
        }

        if ('ResizeObserver' in window) {
            const resizeObserver = new ResizeObserver((entries) => {
                entries.forEach(({ target }) => fitElementText(target));
            });
            fitTextElements.forEach((element) => resizeObserver.observe(element));
        } else {
            window.addEventListener('resize', fitAllTextElements, { passive: true });
        }
    }

    const mobileNavLinks = [...document.querySelectorAll('[data-mobile-nav-link]')];

    function getActiveMobileNavKey(pathname) {
        const path = String(pathname || '/').replace(/\/{2,}/g, '/');
        if (path === '/' || path === '') return 'home';
        if (/^\/courses(?:\/|$)/.test(path)) return 'courses';
        if (/^\/roadmaps(?:\/|$)/.test(path)) return 'roadmaps';
        if (/^\/channels(?:\/|$)/.test(path)) return 'channels';
        if (/^\/contact-us(?:\/|$)/.test(path)) return 'contact';
        if (/^\/about-us(?:\/|$)/.test(path)) return 'about';
        return '';
    }

    if (mobileNavLinks.length) {
        const activeKey = getActiveMobileNavKey(window.location.pathname);
        mobileNavLinks.forEach((link) => {
            const isActive = Boolean(activeKey) && link.dataset.mobileNavLink === activeKey;
            link.classList.toggle('is-active', isActive);
            if (isActive) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
        });
    }

})();
