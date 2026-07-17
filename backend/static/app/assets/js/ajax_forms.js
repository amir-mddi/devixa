(function (window, document, $) {
    "use strict";

    if (!$ || !$.ajax) {
        return;
    }

    const AjaxFormTextVO = Object.freeze({
        incompleteHtml: "The server did not return a complete HTML document.",
        pageLoadFailed: "بارگذاری صفحه با خطا روبه‌رو شد.",
        serverUnavailable: "ارتباط با سرور برقرار نشد.",
        responseRenderFailed: "پاسخ سرور قابل نمایش نبود.",
        formSubmitFailed: "ارسال فرم با خطا روبه‌رو شد.",
    });

    const AjaxFormHeaderVO = Object.freeze({
        ajaxForm: "X-Ajax-Form",
        csrfToken: "X-CSRFToken",
        requestedWith: "X-Requested-With",
        xmlHttpRequest: "XMLHttpRequest",
    });

    const AJAX_MODULE_SCRIPT_TYPE = "application/x-devixa-ajax-module";
    const moduleScopes = new Map();
    let activeRequest = null;
    let navigationSequence = 0;

    const absoluteUrl = (value) => {
        try {
            return new URL(value, window.location.href).href;
        } catch (error) {
            return String(value || "");
        }
    };

    const getCookie = (name) => {
        const prefix = `${name}=`;
        return document.cookie
            .split(";")
            .map((part) => part.trim())
            .find((part) => part.startsWith(prefix))
            ?.slice(prefix.length) || "";
    };

    const createModuleScope = (name) => {
        const previous = moduleScopes.get(name);
        previous?.abort();

        const controller = new AbortController();
        moduleScopes.set(name, controller);
        return controller;
    };

    const executeScriptInScope = (descriptor) => new Promise((resolve) => {
        const moduleName = descriptor.moduleName;
        const controller = createModuleScope(moduleName);
        const originalAddEventListener = EventTarget.prototype.addEventListener;

        EventTarget.prototype.addEventListener = function (type, listener, options) {
            let scopedOptions;
            if (typeof options === "boolean") {
                scopedOptions = {capture: options, signal: controller.signal};
            } else {
                scopedOptions = {...(options || {}), signal: controller.signal};
            }

            try {
                return originalAddEventListener.call(this, type, listener, scopedOptions);
            } catch (error) {
                const result = originalAddEventListener.call(this, type, listener, options);
                controller.signal.addEventListener(
                    "abort",
                    () => this.removeEventListener(type, listener, options),
                    {once: true},
                );
                return result;
            }
        };

        let restored = false;
        const restore = () => {
            if (restored) return;
            restored = true;
            window.clearTimeout(timeoutId);
            EventTarget.prototype.addEventListener = originalAddEventListener;
            resolve();
        };
        const timeoutId = window.setTimeout(restore, 12000);

        const script = document.createElement("script");
        [...descriptor.attributes].forEach(([name, value]) => {
            if (!["src", "type", "data-ajax-module", "data-ajax-script-type"].includes(name)) {
                script.setAttribute(name, value);
            }
        });
        if (descriptor.scriptType) {
            script.type = descriptor.scriptType;
        }
        script.dataset.ajaxRuntimeModule = moduleName;

        if (descriptor.src) {
            const loadsAsynchronously = descriptor.attributes.some(
                ([name]) => name === "async",
            );
            script.src = descriptor.src;
            script.async = loadsAsynchronously;
            script.onload = restore;
            script.onerror = restore;
            document.body.appendChild(script);
            if (loadsAsynchronously) {
                restore();
            }
            return;
        }

        script.textContent = descriptor.text;
        document.body.appendChild(script);
        restore();
    });

    const collectModuleScripts = (nextDocument) => {
        return [...nextDocument.querySelectorAll("script[data-ajax-module]")].map((script) => {
            const declaredType = script.getAttribute("type") || "";
            const scriptType = declaredType === AJAX_MODULE_SCRIPT_TYPE
                ? (script.dataset.ajaxScriptType || "")
                : declaredType;
            return {
                moduleName: script.dataset.ajaxModule,
                src: script.src ? absoluteUrl(script.getAttribute("src")) : "",
                text: script.textContent || "",
                scriptType,
                attributes: [...script.attributes].map((attribute) => [attribute.name, attribute.value]),
            };
        });
    };

    const retainModuleScopes = (moduleNames) => {
        const retained = new Set(moduleNames);
        [...moduleScopes.entries()].forEach(([name, controller]) => {
            if (!retained.has(name)) {
                controller.abort();
                moduleScopes.delete(name);
            }
        });
    };

    const prepareRevealLifecycle = (moduleScripts) => {
        const root = document.documentElement;
        const usesRevealEffects = moduleScripts.some(({moduleName}) => moduleName === "effects");

        root.classList.remove("reveal-pending", "reveal-ready");
        if (!usesRevealEffects) {
            return;
        }

        root.classList.add("reveal-pending");
        window.setTimeout(() => {
            if (!root.classList.contains("reveal-ready")) {
                root.classList.remove("reveal-pending");
            }
        }, 1800);
    };

    const MANAGED_STYLE_SELECTOR = 'link[rel="stylesheet"], style[data-ajax-managed-style]';

    const reconcileStyles = (nextDocument) => {
        const boundary = document.head.querySelector("[data-ajax-style-boundary]");
        const currentLinksByHref = new Map();
        const currentLinks = [...document.head.querySelectorAll('link[rel="stylesheet"]')];

        currentLinks.forEach((link) => {
            const href = absoluteUrl(link.getAttribute("href"));
            const matches = currentLinksByHref.get(href) || [];
            matches.push(link);
            currentLinksByHref.set(href, matches);
        });

        document.head
            .querySelectorAll("style[data-ajax-managed-style]")
            .forEach((style) => style.remove());

        const retainedLinks = new Set();
        const nextStyles = [...nextDocument.head.querySelectorAll(MANAGED_STYLE_SELECTOR)];

        nextStyles.forEach((nextStyle) => {
            let styleNode;
            if (nextStyle.matches('link[rel="stylesheet"]')) {
                const href = absoluteUrl(nextStyle.getAttribute("href"));
                const existingMatches = currentLinksByHref.get(href) || [];
                styleNode = existingMatches.shift() || document.importNode(nextStyle, true);
                currentLinksByHref.set(href, existingMatches);
                retainedLinks.add(styleNode);
            } else {
                styleNode = document.importNode(nextStyle, true);
            }

            document.head.insertBefore(styleNode, boundary || null);
        });

        currentLinks.forEach((link) => {
            if (!retainedLinks.has(link)) {
                link.remove();
            }
        });
    };

    const reconcileHeadMetadata = (nextDocument) => {
        document.title = nextDocument.title || document.title;

        const selector = [
            'meta[name="description"]',
            'meta[name="robots"]',
            'meta[name="theme-color"]',
            'meta[property^="og:"]',
            'meta[name^="twitter:"]',
            'link[rel="canonical"]',
            'link[rel="alternate"][hreflang]',
            'script[type="application/ld+json"]',
        ].join(",");

        document.head.querySelectorAll(selector).forEach((element) => element.remove());
        nextDocument.head.querySelectorAll(selector).forEach((element) => {
            document.head.appendChild(document.importNode(element, true));
        });
    };

    const scheduleFlashRemoval = () => {
        window.setTimeout(() => {
            document.querySelectorAll("[data-project-global-flash]").forEach((stack) => {
                stack.classList.add("project-global-flash--is-hiding");
                window.setTimeout(() => stack.remove(), 450);
            });
        }, 3000);
    };

    const focusPage = () => {
        const hash = window.location.hash;
        if (hash) {
            const target = document.querySelector(hash);
            target?.scrollIntoView({block: "start"});
            return;
        }

        window.scrollTo({top: 0, left: 0, behavior: "auto"});
        const main = document.querySelector("main");
        if (main && !main.hasAttribute("tabindex")) {
            main.setAttribute("tabindex", "-1");
        }
        main?.focus({preventScroll: true});
    };

    const applyHtmlDocument = async (html, responseUrl, {pushHistory = true} = {}) => {
        const parser = new DOMParser();
        const nextDocument = parser.parseFromString(String(html || ""), "text/html");
        if (!nextDocument.body || !nextDocument.body.children.length) {
            throw new Error(AjaxFormTextVO.incompleteHtml);
        }

        const sequence = ++navigationSequence;
        const moduleScripts = collectModuleScripts(nextDocument);
        retainModuleScopes(moduleScripts.map((item) => item.moduleName));
        prepareRevealLifecycle(moduleScripts);

        document.dispatchEvent(new CustomEvent("devixa:before-page-swap"));
        reconcileStyles(nextDocument);
        reconcileHeadMetadata(nextDocument);
        document.documentElement.lang = nextDocument.documentElement.lang || document.documentElement.lang;
        document.documentElement.dir = nextDocument.documentElement.dir || document.documentElement.dir;

        const nextBody = document.importNode(nextDocument.body, true);
        nextBody.querySelectorAll("script").forEach((script) => script.remove());
        document.body.replaceWith(nextBody);

        if (pushHistory && responseUrl) {
            const resolvedUrl = absoluteUrl(responseUrl);
            if (resolvedUrl !== window.location.href) {
                window.history.pushState({ajaxPage: true}, "", resolvedUrl);
            }
        }

        for (const descriptor of moduleScripts) {
            if (sequence !== navigationSequence) {
                return;
            }
            await executeScriptInScope(descriptor);
        }

        scheduleFlashRemoval();
        focusPage();
        document.dispatchEvent(
            new CustomEvent("devixa:page-ready", {
                detail: {url: window.location.href},
            }),
        );
    };

    const messageText = (payload) => {
        if (!payload || typeof payload !== "object") return "";
        return payload.message || payload.detail || payload.fa_msg || payload.error || "";
    };

    const showToast = (message, type = "info") => {
        if (!message) return;
        let stack = document.querySelector("[data-ajax-toast-stack]");
        if (!stack) {
            stack = document.createElement("div");
            stack.className = "ajax-toast-stack";
            stack.dataset.ajaxToastStack = "true";
            stack.setAttribute("aria-live", "polite");
            document.body.appendChild(stack);
        }

        const toast = document.createElement("div");
        toast.className = `ajax-toast ajax-toast--${type}`;
        toast.setAttribute("role", type === "error" ? "alert" : "status");
        toast.textContent = String(message);
        stack.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add("is-visible"));
        window.setTimeout(() => {
            toast.classList.remove("is-visible");
            window.setTimeout(() => toast.remove(), 250);
        }, 3500);
    };

    const clearFieldErrors = (form) => {
        form.querySelectorAll("[data-ajax-field-error]").forEach((element) => element.remove());
        form.querySelectorAll(".ajax-field-invalid").forEach((element) => {
            element.classList.remove("ajax-field-invalid");
            element.removeAttribute("aria-invalid");
        });
    };

    const renderFieldErrors = (form, errors) => {
        clearFieldErrors(form);
        if (!errors || typeof errors !== "object") return false;

        let rendered = false;
        Object.entries(errors).forEach(([fieldName, fieldErrors]) => {
            const messages = Array.isArray(fieldErrors) ? fieldErrors : [fieldErrors];
            const field = form.elements.namedItem(fieldName);
            const anchor = window.RadioNodeList && field instanceof window.RadioNodeList ? field[0] : field;
            if (!anchor || !anchor.parentElement) return;

            anchor.classList.add("ajax-field-invalid");
            anchor.setAttribute("aria-invalid", "true");
            const error = document.createElement("div");
            error.className = "ajax-field-error";
            error.dataset.ajaxFieldError = "true";
            error.textContent = messages.filter(Boolean).join(" ");
            anchor.parentElement.appendChild(error);
            rendered = true;
        });
        return rendered;
    };

    const loadPage = (url, options = {}) => {
        activeRequest?.abort();
        document.body.classList.add("ajax-page-loading");

        activeRequest = $.ajax({
            url: absoluteUrl(url),
            method: "GET",
            headers: {
                [AjaxFormHeaderVO.requestedWith]: AjaxFormHeaderVO.xmlHttpRequest,
            },
            dataType: "html",
        })
            .done((html, _status, xhr) => {
                const requestedUrl = new URL(url, window.location.href);
                const finalUrl = new URL(xhr.responseURL || requestedUrl.href, window.location.href);
                if (requestedUrl.hash && !finalUrl.hash) {
                    finalUrl.hash = requestedUrl.hash;
                }
                applyHtmlDocument(html, finalUrl.href, options).catch((error) => {
                    console.error(error);
                    showToast(AjaxFormTextVO.pageLoadFailed, "error");
                });
            })
            .fail((xhr, status) => {
                if (status !== "abort") {
                    showToast(AjaxFormTextVO.serverUnavailable, "error");
                }
            })
            .always(() => {
                activeRequest = null;
                document.body.classList.remove("ajax-page-loading");
            });

        return activeRequest;
    };

    const responseContentType = (xhr) => String(xhr.getResponseHeader("Content-Type") || "").toLowerCase();

    const handleResponse = (form, payload, xhr) => {
        const contentType = responseContentType(xhr);
        if (contentType.includes("text/html") || typeof payload === "string") {
            return applyHtmlDocument(payload, xhr.responseURL || form.action);
        }

        if (payload && typeof payload === "object") {
            const redirectUrl = payload.redirect_url || payload.redirect || payload.location;
            if (redirectUrl) {
                const destination = new URL(redirectUrl, window.location.href);
                if (destination.origin !== window.location.origin) {
                    window.location.assign(destination.href);
                    return Promise.resolve();
                }
                return loadPage(destination.href);
            }
            if (payload.html) {
                return applyHtmlDocument(payload.html, payload.url || window.location.href);
            }
            const errors = payload.errors || payload.field_errors;
            if (renderFieldErrors(form, errors)) {
                form.querySelector(".ajax-field-invalid")?.focus();
            }
            showToast(messageText(payload), errors ? "error" : "success");
        }
        return Promise.resolve();
    };

    const buildFormData = (form, submitter) => {
        let data;
        try {
            data = submitter ? new FormData(form, submitter) : new FormData(form);
        } catch (error) {
            data = new FormData(form);
            if (submitter?.name) {
                data.append(submitter.name, submitter.value || "");
            }
        }
        return data;
    };

    const setFormBusy = (form, isBusy) => {
        form.classList.toggle("ajax-form-loading", isBusy);
        form.setAttribute("aria-busy", String(isBusy));
        form.querySelectorAll('[type="submit"]').forEach((button) => {
            if (isBusy) {
                button.dataset.ajaxWasDisabled = String(button.disabled);
                button.disabled = true;
            } else {
                const wasDisabled = button.dataset.ajaxWasDisabled === "true";
                button.disabled = wasDisabled;
                delete button.dataset.ajaxWasDisabled;
            }
        });
    };

    const isEligibleForm = (form) => {
        if (!(form instanceof HTMLFormElement)) return false;
        if ((form.dataset.ajax || "").toLowerCase() === "false") return false;
        if ((form.getAttribute("target") || "").toLowerCase() === "_blank") return false;
        if ((form.method || "get").toLowerCase() !== "post") return false;

        const action = new URL(form.action || window.location.href, window.location.href);
        return action.origin === window.location.origin;
    };

    const submitForm = (form, submitter = null) => {
        if (!isEligibleForm(form)) {
            HTMLFormElement.prototype.submit.call(form);
            return null;
        }

        clearFieldErrors(form);
        if (!form.noValidate && !form.checkValidity()) {
            form.reportValidity();
            return null;
        }

        setFormBusy(form, true);
        const request = $.ajax({
            url: form.action || window.location.href,
            method: (form.method || "POST").toUpperCase(),
            data: buildFormData(form, submitter),
            processData: false,
            contentType: false,
            headers: {
                [AjaxFormHeaderVO.requestedWith]: AjaxFormHeaderVO.xmlHttpRequest,
                [AjaxFormHeaderVO.csrfToken]: decodeURIComponent(getCookie("csrftoken")),
                [AjaxFormHeaderVO.ajaxForm]: "true",
            },
        });

        request.done((payload, _status, xhr) => {
            handleResponse(form, payload, xhr).catch((error) => {
                console.error(error);
                showToast(AjaxFormTextVO.responseRenderFailed, "error");
            });
        });

        request.fail((xhr, status) => {
            if (status === "abort") return;
            const contentType = responseContentType(xhr);
            if (contentType.includes("text/html") && xhr.responseText) {
                applyHtmlDocument(xhr.responseText, xhr.responseURL || form.action).catch(() => {
                    showToast(AjaxFormTextVO.formSubmitFailed, "error");
                });
                return;
            }

            const payload = xhr.responseJSON || {};
            const errors = payload.errors || payload.field_errors;
            renderFieldErrors(form, errors);
            showToast(
                messageText(payload) || AjaxFormTextVO.formSubmitFailed,
                "error",
            );
        });

        request.always(() => {
            if (form.isConnected) {
                setFormBusy(form, false);
            }
        });
        return request;
    };

    window.DevixaAjaxForms = Object.freeze({
        submit: submitForm,
        loadPage,
        showToast,
    });

    $(document).on("click.devixaAjaxForms", 'form button[type="submit"], form input[type="submit"]', function () {
        $(this.form).data("ajaxSubmitter", this);
    });

    $(document).on("submit.devixaAjaxForms", "form", function (event) {
        if (event.isDefaultPrevented() || !isEligibleForm(this)) return;
        event.preventDefault();
        const submitter = event.originalEvent?.submitter || $(this).data("ajaxSubmitter") || null;
        $(this).removeData("ajaxSubmitter");
        submitForm(this, submitter);
    });

    window.addEventListener("popstate", () => {
        loadPage(window.location.href, {pushHistory: false});
    });

    const bootInitialModules = async () => {
        const moduleScripts = collectModuleScripts(document);
        retainModuleScopes(moduleScripts.map((item) => item.moduleName));
        document.querySelectorAll("script[data-ajax-module]").forEach((script) => script.remove());

        for (const descriptor of moduleScripts) {
            await executeScriptInScope(descriptor);
        }

        scheduleFlashRemoval();
        document.dispatchEvent(
            new CustomEvent("devixa:page-ready", {
                detail: {url: window.location.href, initial: true},
            }),
        );
    };

    $(bootInitialModules);
})(window, document, window.jQuery);
