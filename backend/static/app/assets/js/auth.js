(() => {
    "use strict";

    const root = document.documentElement;
    const body = document.body;
    const themeToggle = document.querySelector("[data-auth-theme-toggle]");

    const applyTheme = (theme) => {
        const normalized = theme === "light" ? "light" : "dark";
        root.dataset.theme = normalized;
        root.style.colorScheme = normalized;
        body.dataset.theme = normalized;
        body.classList.toggle("light-theme", normalized === "light");
        try {
            localStorage.setItem("theme", normalized);
        } catch (error) {
            // Theme still applies when storage is blocked by the browser.
        }
        document.querySelector('meta[name="theme-color"]')?.setAttribute(
            "content",
            normalized === "light" ? "#f5f7ff" : "#070b14",
        );
    };

    applyTheme(root.dataset.theme || "dark");
    themeToggle?.addEventListener("click", () => {
        applyTheme(root.dataset.theme === "light" ? "dark" : "light");
    });



    const recaptchaEnabled = body.dataset.recaptchaEnabled === "true";
    const recaptchaSiteKey = (body.dataset.recaptchaSiteKey || "").trim();
    const recaptchaErrorMessage = body.dataset.recaptchaErrorMessage || "";

    const setRecaptchaFormBusy = (form, isBusy) => {
        form.setAttribute("aria-busy", isBusy ? "true" : "false");
        const submitButtons = form.querySelectorAll('[type="submit"]');
        submitButtons.forEach((button) => {
            button.disabled = isBusy;
            button.classList.toggle("is-loading", isBusy);
        });
    };

    const showRecaptchaClientError = (form) => {
        const errorElement = form.querySelector("[data-recaptcha-client-error]");
        if (!errorElement) return;
        errorElement.textContent = recaptchaErrorMessage;
        errorElement.hidden = false;
    };

    const clearRecaptchaClientError = (form) => {
        const errorElement = form.querySelector("[data-recaptcha-client-error]");
        if (!errorElement) return;
        errorElement.textContent = "";
        errorElement.hidden = true;
    };

    const executeRecaptcha = (action) => new Promise((resolve, reject) => {
        if (!window.grecaptcha || typeof window.grecaptcha.ready !== "function") {
            reject(new Error("recaptcha_not_loaded"));
            return;
        }

        window.grecaptcha.ready(() => {
            window.grecaptcha
                .execute(recaptchaSiteKey, {action})
                .then(resolve)
                .catch(reject);
        });
    });

    if (recaptchaEnabled && recaptchaSiteKey) {
        document.querySelectorAll("[data-recaptcha-config]").forEach((configElement) => {
            const form = configElement.closest("form");
            const tokenInput = form?.querySelector("[data-recaptcha-token]");
            const action = (configElement.dataset.recaptchaAction || "").trim();
            if (!form || !tokenInput || !action) return;

            form.addEventListener("submit", async (event) => {
                event.preventDefault();
                clearRecaptchaClientError(form);
                setRecaptchaFormBusy(form, true);

                try {
                    const token = await executeRecaptcha(action);
                    if (!token) throw new Error("empty_recaptcha_token");
                    tokenInput.value = token;
                    HTMLFormElement.prototype.submit.call(form);
                } catch (error) {
                    tokenInput.value = "";
                    showRecaptchaClientError(form);
                    setRecaptchaFormBusy(form, false);
                }
            });
        });
    }

    document.querySelectorAll("[data-recovery-form]").forEach((form) => {
        const methodInputs = [...form.querySelectorAll("[data-recovery-method]")];
        const panels = [...form.querySelectorAll("[data-recovery-panel]")];
        const resendForm = document.querySelector("[data-recovery-resend]");

        const sync = () => {
            const selected = methodInputs.find((input) => input.checked)?.value || "email";
            panels.forEach((panel) => {
                const active = panel.dataset.recoveryPanel === selected;
                panel.hidden = !active;
                panel.querySelectorAll("input").forEach((input) => {
                    input.disabled = !active;
                });
            });

            if (resendForm) {
                const methodField = resendForm.querySelector("[data-resend-method]");
                const emailField = resendForm.querySelector("[data-resend-email]");
                const phoneField = resendForm.querySelector("[data-resend-phone]");
                if (methodField) methodField.value = selected;
                const activeEmail = form.querySelector('[data-recovery-panel="email"] input');
                const activePhone = form.querySelector('[data-recovery-panel="sms"] input');
                if (emailField && activeEmail) emailField.value = activeEmail.value;
                if (phoneField && activePhone) phoneField.value = activePhone.value;
            }
        };

        methodInputs.forEach((input) => input.addEventListener("change", sync));
        form.addEventListener("input", sync);
        sync();
    });
})();
