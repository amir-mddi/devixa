(() => {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        if (!window.DevixaCatalogController) return;

        new window.DevixaCatalogController({
            rootSelector: '.roadmaps_categories',
            itemSelector: '.roadmap_link',
            categorySelector: '.roadmaps_hero .category_chips .chip a',
            allCategoryId: 'all_maps',
            defaultPageSize: 6,
            itemLabel: 'نقشه راه',
        }).init();
    });
})();
