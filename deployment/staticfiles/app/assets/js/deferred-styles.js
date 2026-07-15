(() => {
    "use strict";

    const activateStylesheet = (link) => {
        link.rel = "stylesheet";
        link.media = "all";
        link.removeAttribute("as");
        link.removeAttribute("fetchpriority");
        link.removeAttribute("data-deferred-stylesheet");
    };

    document
        .querySelectorAll("link[data-deferred-stylesheet]")
        .forEach(activateStylesheet);
})();
