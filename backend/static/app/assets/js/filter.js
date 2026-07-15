(() => {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        if (!window.ProjectCatalogController) return;

        new window.ProjectCatalogController({
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
