(() => {
    'use strict';

    const fullMenu = document.getElementById('site-mobile-menu');
    const fullMenuToggle = document.querySelector('.site-menu-toggle');
    const mobileBackdrop = document.querySelector('[data-site-mobile-backdrop]');

    function isDesktopViewport() {
        return window.matchMedia('(min-width: 981px)').matches;
    }

    function setFullMenuState(isOpen) {
        if (!fullMenu || !fullMenuToggle) return;
        const open = Boolean(isOpen) && !isDesktopViewport();
        fullMenu.hidden = !open;
        fullMenu.classList.toggle('is-open', open);
        fullMenuToggle.setAttribute('aria-expanded', String(open));
        fullMenuToggle.setAttribute('aria-label', open ? 'بستن منو' : 'نمایش همه منوها');
        document.body.classList.toggle('site-mobile-menu-open', open);
        if (mobileBackdrop) mobileBackdrop.hidden = !open;
        if (open) fullMenu.querySelector('a')?.focus({ preventScroll: true });
    }

    function closeFullMenu() {
        setFullMenuState(false);
    }

    function toggleFullMenu() {
        if (!fullMenu || !fullMenuToggle) return;
        const isOpen = !fullMenu.hidden && fullMenu.classList.contains('is-open');
        setFullMenuState(!isOpen);
    }

    if (fullMenu && fullMenuToggle) {
        setFullMenuState(false);
        fullMenuToggle.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            toggleFullMenu();
        });
        fullMenu.addEventListener('click', (event) => {
            if (event.target.closest('a')) closeFullMenu();
        });
        mobileBackdrop?.addEventListener('click', closeFullMenu);
        document.addEventListener('click', (event) => {
            if (!event.target.closest('.site-mobile-menu, .site-menu-toggle')) closeFullMenu();
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                closeFullMenu();
                fullMenuToggle.focus();
            }
        });
        window.addEventListener('resize', () => {
            if (isDesktopViewport()) closeFullMenu();
        }, { passive: true });
    }

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
        if (/^\/(?:mentors|mentorship)(?:\/|$)/.test(path)) return 'mentors';
        if (/^\/academies(?:\/|$)/.test(path)) return 'academies';
        if (/^\/opportunities(?:\/|$)/.test(path)) return 'opportunities';
        if (/^\/my-marketplace(?:\/|$)/.test(path)) return 'mentors';
        if (/^\/collaborations(?:\/|$)/.test(path)) return 'mentors';
        if (/^\/roadmaps(?:\/|$)/.test(path)) return 'roadmaps';
        if (/^\/channels(?:\/|$)/.test(path)) return 'channels';
        if (/^\/contact-us(?:\/|$)/.test(path)) return 'contact';
        if (/^\/(?:articles|blog|news)(?:\/|$)/.test(path)) return 'articles';
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
