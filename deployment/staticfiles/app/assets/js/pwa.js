(() => {
    "use strict";

    if (!("serviceWorker" in navigator) || !window.isSecureContext) return;

    const register = () => {
        navigator.serviceWorker.register("/service-worker.js", {scope: "/"}).catch(() => {
            // Progressive enhancement: the website remains fully functional.
        });
    };

    if ("requestIdleCallback" in window) {
        window.requestIdleCallback(register, {timeout: 4000});
    } else {
        window.addEventListener("load", register, {once: true});
    }
})();
