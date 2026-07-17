(() => {
    'use strict';

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const projectName = document.body?.dataset?.projectName || document.title || 'Project';
    const projectInitial = document.body?.dataset?.projectInitial || projectName.trim().charAt(0).toUpperCase() || 'P';
    const $ = (selector, scope = document) => scope.querySelector(selector);
    const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];

    document.documentElement.classList.add('premium-ready');

    function onReady(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback, { once: true });
        } else {
            callback();
        }
    }

    function safeRAF(callback) {
        let ticking = false;
        return (...args) => {
            if (ticking) return;
            ticking = true;
            requestAnimationFrame(() => {
                callback(...args);
                ticking = false;
            });
        };
    }

    function createAmbient() {
        if ($('.project-ambient')) return;
        const ambient = document.createElement('div');
        ambient.className = 'project-ambient';
        ambient.setAttribute('aria-hidden', 'true');
        ambient.innerHTML = '<span></span><span></span><span></span>';
        document.body.prepend(ambient);
    }

    function createPreloader() {
        if (prefersReducedMotion || $('.project-preloader')) return;
        document.body.classList.add('page-is-loading');
        const preloader = document.createElement('section');
        preloader.className = 'project-preloader';
        preloader.setAttribute('aria-live', 'polite');
        preloader.innerHTML = `
            <div class="project-preloader__card">
                <div class="project-preloader__logo">${projectInitial}</div>
                <h2 class="project-preloader__title">${projectName} Experience</h2>
                <p class="subtitle" style="width:100%;font-size:14px">در حال آماده‌سازی تجربه‌ای نرم، سریع و حرفه‌ای...</p>
                <div class="project-preloader__bar"><span></span></div>
            </div>`;
        document.body.appendChild(preloader);
        window.addEventListener('load', () => hidePreloader(preloader), { once: true });
        setTimeout(() => hidePreloader(preloader), 900);
    }

    function hidePreloader(preloader) {
        preloader.classList.add('is-hidden');
        document.body.classList.remove('page-is-loading');
        document.body.classList.add('is-loaded');
        setTimeout(() => preloader.remove(), 650);
    }

    function enhanceNavigation() {
        const nav = $('#menubar');
        const links = $$('.navbar .menu a');
        const currentPath = location.pathname.split('/').pop() || 'index.html';

        links.forEach((link) => {
            const href = link.getAttribute('href');
            if (href && href !== '#' && href.split('/').pop() === currentPath) {
                link.classList.add('is-active');
                link.setAttribute('aria-current', 'page');
            }
        });

        if (!nav) return;
        const updateNav = safeRAF(() => {
            nav.classList.toggle('is-scrolled', window.scrollY > 12);
        });
        updateNav();
        window.addEventListener('scroll', updateNav, { passive: true });
    }

    function createScrollProgress() {
        if ($('.site-scroll-progress')) return;
        const progress = document.createElement('div');
        progress.className = 'site-scroll-progress';
        progress.setAttribute('aria-hidden', 'true');
        document.body.appendChild(progress);
        const update = safeRAF(() => {
            const height = document.documentElement.scrollHeight - window.innerHeight;
            const ratio = height > 0 ? Math.min(window.scrollY / height, 1) : 0;
            progress.style.transform = `scaleX(${ratio})`;
        });
        update();
        window.addEventListener('scroll', update, { passive: true });
        window.addEventListener('resize', update);
    }

    function createBackToTop() {
        if ($('.back-to-top')) return;
        const button = document.createElement('button');
        button.className = 'back-to-top';
        button.type = 'button';
        button.setAttribute('aria-label', 'بازگشت به بالای صفحه');
        button.innerHTML = '↑';
        document.body.appendChild(button);
        button.addEventListener('click', () => window.scrollTo({ top: 0, behavior: prefersReducedMotion ? 'auto' : 'smooth' }));
        const update = safeRAF(() => button.classList.toggle('is-visible', window.scrollY > 520));
        update();
        window.addEventListener('scroll', update, { passive: true });
    }

    function createCursorGlow() {
        if (prefersReducedMotion || !window.matchMedia('(pointer:fine)').matches || $('.cursor-glow')) return;
        const glow = document.createElement('div');
        glow.className = 'cursor-glow';
        glow.setAttribute('aria-hidden', 'true');
        document.body.appendChild(glow);
        const move = safeRAF((event) => {
            glow.style.left = `${event.clientX}px`;
            glow.style.top = `${event.clientY}px`;
        });
        window.addEventListener('pointermove', move, { passive: true });
    }

    function addRippleEffect() {
        const selectors = [
            'a.starting', 'a.courses_link', '.course_btn', '.Registration',
            '.btn_start', '.btn_primary', 'input.submit', '.category_chips .chip a',
            '.navbar .nav_cta a'
        ].join(',');
        document.addEventListener('click', (event) => {
            const target = event.target.closest(selectors);
            if (!target || target.tagName === 'INPUT' || prefersReducedMotion) return;
            const rect = target.getBoundingClientRect();
            const ripple = document.createElement('span');
            const size = Math.max(rect.width, rect.height);
            ripple.setAttribute('data-ripple', '');
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${event.clientX - rect.left - size / 2}px`;
            ripple.style.top = `${event.clientY - rect.top - size / 2}px`;
            target.appendChild(ripple);
            ripple.addEventListener('animationend', () => ripple.remove(), { once: true });
        });
    }

    function revealEverything() {
        const candidates = $$([
            '.course_card', '.roadmap_link', '.stat_card', '.card_process', '.about_cards .card',
            '.history_cards .card', '.contact_cards .card', '.curriculum .card', '.card_learn',
            '.roadmap_skills .card', '.roadmap_projects .card', '.faq_item', '.footer_section',
            '[data-premium-reveal]'
        ].join(','));

        candidates.forEach((item, index) => {
            if (!item.hasAttribute('data-premium-reveal')) {
                item.setAttribute('data-premium-reveal', '');
                item.style.transitionDelay = `${Math.min(index % 8, 6) * 45}ms`;
            }
        });

        if (!('IntersectionObserver' in window) || prefersReducedMotion) {
            candidates.forEach((item) => item.classList.add('is-visible'));
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

        candidates.forEach((item) => observer.observe(item));
    }

    function addTilt() {
        if (prefersReducedMotion || !window.matchMedia('(pointer:fine)').matches) return;
        const items = $$('.course_card, .roadmaps_categories .card, .hero_section .left_hero .mockup, .dashboard_mockup, .roadmap_hero .map');
        items.forEach((card) => {
            card.classList.add('premium-tilt');
            card.addEventListener('pointermove', (event) => {
                const rect = card.getBoundingClientRect();
                const x = (event.clientX - rect.left) / rect.width - 0.5;
                const y = (event.clientY - rect.top) / rect.height - 0.5;
                card.style.transform = `translateY(-8px) rotateX(${(-y * 7).toFixed(2)}deg) rotateY(${(x * 7).toFixed(2)}deg)`;
            }, { passive: true });
            card.addEventListener('pointerleave', () => {
                card.style.transform = '';
            });
        });
    }

    function improveForms() {
        $$('input, textarea').forEach((input) => {
            if (!input.getAttribute('autocomplete')) {
                if (input.type === 'email') input.setAttribute('autocomplete', 'email');
                if (input.type === 'password') input.setAttribute('autocomplete', 'current-password');
                if (input.name?.toLowerCase().includes('fname')) input.setAttribute('autocomplete', 'given-name');
                if (input.name?.toLowerCase().includes('lname')) input.setAttribute('autocomplete', 'family-name');
                if (input.name?.toLowerCase().includes('username')) input.setAttribute('autocomplete', 'username');
            }
            if (input.placeholder && !input.getAttribute('aria-label')) {
                input.setAttribute('aria-label', input.placeholder);
            }
        });

        $$('form').forEach((form) => {
            form.addEventListener('submit', (event) => {
                if (form.getAttribute('action') === '#' || form.getAttribute('method') === '#') {
                    event.preventDefault();
                    showToast('این فرم نمایشی است؛ اتصال به بک‌اند برای ارسال واقعی لازم است.');
                }
            });
        });
    }

    function showToast(message) {
        let toast = $('.project-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'project-toast';
            toast.setAttribute('role', 'status');
            toast.setAttribute('aria-live', 'polite');
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.classList.add('is-visible');
        clearTimeout(showToast.timer);
        showToast.timer = setTimeout(() => toast.classList.remove('is-visible'), 3200);
    }

    function improveFilterFeedback() {
        const containers = $$('.courses_catalog .courses, .roadmaps_categories .categories');
        if (!containers.length) return;
        const markFiltering = () => {
            containers.forEach((container) => {
                container.classList.remove('is-filtering');
                void container.offsetWidth;
                container.classList.add('is-filtering');
                setTimeout(() => container.classList.remove('is-filtering'), 420);
            });
        };
        $$('.category_chips a, #search_box').forEach((control) => {
            const eventName = control.matches('input') ? 'input' : 'click';
            control.addEventListener(eventName, markFiltering, { passive: eventName !== 'click' });
        });
    }

    function polishCourseMetrics() {
        $$('.price, #course_price, .time, .level').forEach((item) => {
            item.setAttribute('data-premium-reveal', '');
        });
    }

    function normalizeDigits(value) {
        const persian = '۰۱۲۳۴۵۶۷۸۹';
        const arabic = '٠١٢٣٤٥٦٧٨٩';

        return String(value || '')
            .replace(/[۰-۹]/g, (digit) => persian.indexOf(digit))
            .replace(/[٠-٩]/g, (digit) => arabic.indexOf(digit));
    }

    function toFaNumber(value) {
        return Math.round(value).toLocaleString('fa-IR');
    }

    function buildCounterData(element) {
        const text = element.textContent.trim();
        if (!text || text.length > 48 || element.dataset.counterReady === 'true') return null;

        const normalizedText = normalizeDigits(text);
        if (/\+?98[\s-]?9\d{9}/.test(normalizedText.replace(/\s/g, ''))) return null;

        const match = text.match(/(\+)?\s*([0-9۰-۹٠-٩][0-9۰-۹٠-٩,،٬.\s]*)(\+)?\s*([٪%])?/);
        if (!match) return null;

        const numberPart = normalizeDigits(match[2]).replace(/[^0-9]/g, '');
        if (!numberPart) return null;

        const target = Number(numberPart);
        if (!Number.isFinite(target) || target <= 0 || target > 10000000) return null;

        return {
            original: text,
            target,
            before: text.slice(0, match.index),
            after: text.slice(match.index + match[0].length),
            prefix: match[1] || '',
            suffixPlus: match[3] || '',
            percent: match[4] || '',
        };
    }

    function renderCounter(element, data, value) {
        const formatted = `${data.prefix}${toFaNumber(value)}${data.suffixPlus}${data.percent}`;
        element.textContent = `${data.before}${formatted}${data.after}`;
    }

    function animateCounter(element, data) {
        if (element.dataset.counterDone === 'true') return;
        element.dataset.counterDone = 'true';
        element.classList.add('premium-counting');

        if (prefersReducedMotion) {
            renderCounter(element, data, data.target);
            return;
        }

        const duration = Math.min(1050, Math.max(620, data.target > 1000 ? 920 : 720));
        const start = performance.now();

        const tick = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            renderCounter(element, data, data.target * eased);

            if (progress < 1) {
                requestAnimationFrame(tick);
            } else {
                renderCounter(element, data, data.target);
            }
        };

        renderCounter(element, data, 0);
        requestAnimationFrame(tick);
    }

    function animateNumbers() {
        const selectors = [
            '.stat_card h4',
            '.stat_card .title',
            '.hero_section .right_hero p span',
            '.badge h4',
            '.teacher .title',
            '.teacher h4',
            '.course_info h4',
            '.course_info strong',
            '#course_price',
            '.price:not(a)',
            '.time',
            '.level'
        ].join(',');

        const candidates = $$(selectors)
            .filter((element) => !element.closest('.catalog_toolbar, .catalog_pagination, select, option, input, textarea'));

        const items = candidates
            .map((element) => ({ element, data: buildCounterData(element) }))
            .filter((item) => item.data);

        items.forEach(({ element, data }) => {
            element.dataset.counterReady = 'true';

            if (!('IntersectionObserver' in window) || prefersReducedMotion) {
                animateCounter(element, data);
                return;
            }

            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    animateCounter(element, data);
                    observer.disconnect();
                });
            }, { threshold: 0.35, rootMargin: '0px 0px -5% 0px' });

            observer.observe(element);
        });
    }

    function keyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            if (event.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
                const search = $('#search_box');
                if (search) {
                    event.preventDefault();
                    search.focus();
                    showToast('جستجوی سریع فعال شد.');
                }
            }
        });
    }

    onReady(() => {
        createPreloader();
        createAmbient();
        enhanceNavigation();
        createScrollProgress();
        createBackToTop();
        createCursorGlow();
        addRippleEffect();
        polishCourseMetrics();
        revealEverything();
        addTilt();
        improveForms();
        improveFilterFeedback();
        animateNumbers();
        keyboardShortcuts();
    });
})();
