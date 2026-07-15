(() => {
    'use strict';

    const noop = () => undefined;
    const toArray = (selector, parent = document) => [...parent.querySelectorAll(selector)];
    const toFaNumber = (value) => Number(value || 0).toLocaleString('fa-IR');

    class ProjectCatalogController {
        constructor(options) {
            this.root = document.querySelector(options.rootSelector);
            this.itemSelector = options.itemSelector;
            this.searchSelector = options.searchSelector || null;
            this.categorySelector = options.categorySelector;
            this.allCategoryId = options.allCategoryId;
            this.defaultPageSize = Number(options.defaultPageSize || 6);
            this.itemLabel = options.itemLabel || 'آیتم';
            this.onPageChange = options.onPageChange || noop;
            this.endpoint = options.endpoint || this.root?.dataset.apiEndpoint || '';
            this.mode = options.mode || this.root?.dataset.paginationMode || 'client';

            this.items = [];
            this.state = {
                category: 'all',
                search: '',
                page: 1,
                pageSize: this.defaultPageSize,
            };
        }

        init() {
            if (!this.root) return;

            this.grid = this.root.querySelector('[data-catalog-grid]');
            this.notFound = this.root.querySelector('#not_found');
            this.pagination = this.root.querySelector('[data-pagination]');
            this.count = this.root.querySelector('[data-catalog-count]');
            this.summary = this.root.querySelector('[data-catalog-summary]');
            this.pageSize = this.root.querySelector('[data-page-size]');
            this.search = this.searchSelector ? document.querySelector(this.searchSelector) : null;
            this.categoryLinks = toArray(this.categorySelector);
            this.items = toArray(this.itemSelector, this.root).map((element) => this.mapItem(element));

            if (this.pageSize) {
                this.enhancePageSizeSelect();
                this.state.pageSize = Number(this.pageSize.value || this.defaultPageSize);
                this.pageSize.addEventListener('change', () => {
                    this.state.pageSize = Number(this.pageSize.value || this.defaultPageSize);
                    this.state.page = 1;
                    this.syncPremiumSelect();
                    this.render();
                });
            }

            if (this.search) {
                this.search.setAttribute('dir', 'rtl');
                this.search.setAttribute('autocomplete', 'off');
                this.search.addEventListener('input', () => {
                    this.state.search = this.normalize(this.search.value);
                    this.state.page = 1;
                    this.render();
                });
            }

            this.categoryLinks.forEach((link) => {
                link.addEventListener('click', (event) => {
                    event.preventDefault();
                    this.state.category = this.resolveCategory(link);
                    this.state.page = 1;
                    this.setActiveCategory(link);
                    this.render();
                });
            });

            const initialActiveLink = this.categoryLinks.find((link) => link.classList.contains('active')) || this.categoryLinks[0];
            if (initialActiveLink) {
                this.state.category = this.resolveCategory(initialActiveLink);
                this.setActiveCategory(initialActiveLink);
            }

            this.render();
        }

        mapItem(element) {
            const title = element.dataset.title || element.querySelector('h1,h2,h3,h4')?.textContent || '';
            const description = element.querySelector('p')?.textContent || '';
            const category = element.dataset.category || element.id || 'all';
            const categoryLabel = element.dataset.categoryLabel || category;

            return {
                element,
                title,
                category,
                categoryLabel,
                searchableText: this.normalize(`${title} ${description} ${categoryLabel}`),
            };
        }

        normalize(value) {
            return String(value || '')
                .toLowerCase()
                .replace(/[ي]/g, 'ی')
                .replace(/[ك]/g, 'ک')
                .trim();
        }

        resolveCategory(link) {
            const id = link.id || '';
            if (id === this.allCategoryId || id.startsWith('all_')) return 'all';
            return id
                .replace('_courses', '')
                .replace('_course', '')
                .replace('_maps', '')
                .replace('_map', '');
        }

        setActiveCategory(activeLink) {
            this.categoryLinks.forEach((link) => {
                const isActive = link === activeLink;
                link.classList.toggle('active', isActive);
                link.setAttribute('aria-pressed', String(isActive));
            });
        }

        enhancePageSizeSelect() {
            const select = this.pageSize;
            if (!select || select.dataset.premiumSelect === 'ready') return;

            select.dataset.premiumSelect = 'ready';
            select.classList.add('catalog_native_select');

            const wrapper = document.createElement('div');
            wrapper.className = 'premium_select';

            const trigger = document.createElement('button');
            trigger.type = 'button';
            trigger.className = 'premium_select__trigger';
            trigger.setAttribute('aria-haspopup', 'listbox');
            trigger.setAttribute('aria-expanded', 'false');

            const menu = document.createElement('div');
            menu.className = 'premium_select__menu';
            menu.setAttribute('role', 'listbox');
            menu.setAttribute('tabindex', '-1');

            const close = () => {
                wrapper.classList.remove('is-open');
                trigger.setAttribute('aria-expanded', 'false');
            };

            const open = () => {
                document.querySelectorAll('.premium_select.is-open').forEach((item) => {
                    if (item !== wrapper) item.classList.remove('is-open');
                });
                wrapper.classList.add('is-open');
                trigger.setAttribute('aria-expanded', 'true');
            };

            [...select.options].forEach((option) => {
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'premium_select__option';
                item.setAttribute('role', 'option');
                item.dataset.value = option.value;
                item.textContent = option.textContent.trim();
                item.addEventListener('click', () => {
                    select.value = option.value;
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                    close();
                    trigger.focus({ preventScroll: true });
                });
                menu.appendChild(item);
            });

            trigger.addEventListener('click', (event) => {
                event.preventDefault();
                wrapper.classList.contains('is-open') ? close() : open();
            });

            trigger.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') close();
                if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    open();
                    menu.querySelector('.premium_select__option.is-selected')?.focus({ preventScroll: true });
                }
            });

            menu.addEventListener('keydown', (event) => {
                const options = [...menu.querySelectorAll('.premium_select__option')];
                const currentIndex = options.indexOf(document.activeElement);

                if (event.key === 'Escape') {
                    close();
                    trigger.focus({ preventScroll: true });
                }

                if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                    event.preventDefault();
                    const direction = event.key === 'ArrowDown' ? 1 : -1;
                    const nextIndex = currentIndex < 0
                        ? 0
                        : (currentIndex + direction + options.length) % options.length;
                    options[nextIndex]?.focus({ preventScroll: true });
                }
            });

            document.addEventListener('click', (event) => {
                if (!wrapper.contains(event.target)) close();
            });

            wrapper.append(trigger, menu);
            select.insertAdjacentElement('afterend', wrapper);
            this.premiumSelect = { wrapper, trigger, menu };
            this.syncPremiumSelect();
        }

        syncPremiumSelect() {
            if (!this.premiumSelect || !this.pageSize) return;

            const selectedOption = this.pageSize.selectedOptions[0];
            const label = selectedOption?.textContent.trim() || this.pageSize.value;

            this.premiumSelect.trigger.innerHTML = `<span>${label}</span>`;
            this.premiumSelect.menu.querySelectorAll('.premium_select__option').forEach((option) => {
                const isSelected = option.dataset.value === this.pageSize.value;
                option.classList.toggle('is-selected', isSelected);
                option.setAttribute('aria-selected', String(isSelected));
            });
        }

        getFilteredItems() {
            return this.items.filter((item) => {
                const categoryMatched = this.state.category === 'all' || item.category === this.state.category;
                const searchMatched = !this.state.search || item.searchableText.includes(this.state.search);
                return categoryMatched && searchMatched;
            });
        }

        render() {
            const filtered = this.getFilteredItems();
            const total = filtered.length;
            const totalPages = Math.max(Math.ceil(total / this.state.pageSize), 1);
            this.state.page = Math.min(this.state.page, totalPages);

            const fromIndex = (this.state.page - 1) * this.state.pageSize;
            const visibleItems = filtered.slice(fromIndex, fromIndex + this.state.pageSize);
            const visibleElements = new Set(visibleItems.map((item) => item.element));

            if (this.grid) this.grid.setAttribute('aria-busy', 'true');

            this.items.forEach((item) => {
                const isVisible = visibleElements.has(item.element);
                item.element.classList.toggle('d-none', !isVisible);
                item.element.classList.toggle('d-block', isVisible);
                item.element.toggleAttribute('hidden', !isVisible);
            });

            if (this.notFound) {
                this.notFound.classList.toggle('d-none', total > 0);
                this.notFound.classList.toggle('d-block', total === 0);
            }

            this.renderStatus(total, fromIndex, visibleItems.length);
            this.renderPagination(totalPages);
            this.emitPageChange(total);

            window.requestAnimationFrame(() => {
                if (this.grid) this.grid.setAttribute('aria-busy', 'false');
            });
        }

        renderStatus(total, fromIndex, visibleCount) {
            const start = total === 0 ? 0 : fromIndex + 1;
            const end = total === 0 ? 0 : fromIndex + visibleCount;

            if (this.count) {
                this.count.textContent = `نمایش ${toFaNumber(start)} تا ${toFaNumber(end)} از ${toFaNumber(total)} ${this.itemLabel}`;
            }

            if (!this.summary) return;

            const categoryTitle = this.state.category === 'all'
                ? 'همه دسته‌ها'
                : this.items.find((item) => item.category === this.state.category)?.categoryLabel || this.state.category;
            const searchTitle = this.state.search ? `، جستجو: «${this.search?.value.trim()}»` : '';
            this.summary.textContent = `${categoryTitle}${searchTitle} — صفحه ${toFaNumber(this.state.page)}`;
        }

        renderPagination(totalPages) {
            if (!this.pagination) return;
            this.pagination.innerHTML = '';
            this.pagination.hidden = totalPages <= 1;

            if (totalPages <= 1) return;

            const fragment = document.createDocumentFragment();
            fragment.appendChild(this.createButton('قبلی', this.state.page - 1, this.state.page === 1, 'prev'));

            this.getPageWindow(totalPages).forEach((page) => {
                if (page === 'dots') {
                    const dots = document.createElement('span');
                    dots.className = 'pagination_dots';
                    dots.textContent = '…';
                    dots.setAttribute('aria-hidden', 'true');
                    fragment.appendChild(dots);
                    return;
                }
                fragment.appendChild(this.createButton(toFaNumber(page), page, false, 'page'));
            });

            fragment.appendChild(this.createButton('بعدی', this.state.page + 1, this.state.page === totalPages, 'next'));
            this.pagination.appendChild(fragment);
        }

        getPageWindow(totalPages) {
            if (totalPages <= 5) return Array.from({ length: totalPages }, (_, index) => index + 1);

            const current = this.state.page;
            const pages = new Set([1, totalPages, current, current - 1, current + 1]);
            const sorted = [...pages].filter((page) => page >= 1 && page <= totalPages).sort((a, b) => a - b);
            const output = [];

            sorted.forEach((page, index) => {
                if (index > 0 && page - sorted[index - 1] > 1) output.push('dots');
                output.push(page);
            });

            return output;
        }

        createButton(label, page, disabled, type) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `pagination_btn pagination_btn--${type}`;
            button.textContent = label;
            button.disabled = disabled;
            button.setAttribute('aria-label', type === 'page' ? `رفتن به صفحه ${label}` : label);

            if (type === 'page' && page === this.state.page) {
                button.classList.add('is-active');
                button.setAttribute('aria-current', 'page');
            }

            button.addEventListener('click', () => {
                if (disabled || page === this.state.page) return;
                this.state.page = page;
                this.render();
                this.root.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });

            return button;
        }

        emitPageChange(total) {
            const detail = {
                page: this.state.page,
                pageSize: this.state.pageSize,
                category: this.state.category,
                search: this.search?.value.trim() || '',
                total,
                endpoint: this.endpoint,
                mode: this.mode,
            };

            this.root.dispatchEvent(new CustomEvent('project:catalog:page-change', { detail }));
            this.onPageChange(detail);
        }
    }

    window.ProjectCatalogController = ProjectCatalogController;
})();
