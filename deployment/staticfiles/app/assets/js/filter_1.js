(() => {
    "use strict";

    const initializeRoadmapCatalog = () => {
        if (!window.ProjectCatalogController) {
            return;
        }

        new window.ProjectCatalogController({
            rootSelector: ".roadmaps_categories",
            itemSelector: ".roadmap_link",
            categorySelector: ".roadmaps_hero .category_chips .chip a",
            allCategoryId: "all_maps",
            defaultPageSize: 6,
            itemLabel: "نقشه راه",
        }).init();
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeRoadmapCatalog, {once: true});
    } else {
        initializeRoadmapCatalog();
    }
})();
