(() => {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        if (!window.DevixaCatalogController) return;

        new window.DevixaCatalogController({
            rootSelector: '.courses_catalog',
            itemSelector: '.course_card',
            categorySelector: '.courses_section .category_chips .chip a',
            searchSelector: '#search_box',
            allCategoryId: 'all_courses',
            defaultPageSize: 6,
            itemLabel: 'دوره',
        }).init();
    });
})();
