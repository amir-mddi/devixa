"""Offline Chromium smoke tests for Devixa's real theme and AJAX source files.

Uses set_content because this environment may prohibit local HTTP navigation.
This checks frontend behavior only; it does NOT assert real Django auth/DB/static serving.
Run: python backend/tests/smoke_theme_navigation.py
"""
from __future__ import annotations

import base64
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "backend/static/app/assets"
BOOTSTRAP = (ROOT / "backend/templates/web/shared/_theme_bootstrap.html").read_text()
VARS = (ASSETS / "Styles/variables.css").read_text()
THEME_JS = (ASSETS / "js/theme.js").read_text()
AUTH_JS = (ASSETS / "js/auth.js").read_text()
AJAX_JS = (ASSETS / "js/ajax_forms.js").read_text()
JQUERY_JS = (ASSETS / "vendor/jquery/jquery-3.7.1.min.js").read_text()


def data_url(content: str, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(content.encode()).decode()}"


def document(kind: str, *, style='') -> str:
    script = f'<script type="application/x-devixa-ajax-module" data-ajax-module="{kind}" src="{data_url(AUTH_JS if kind == "auth" else THEME_JS, "text/javascript")}"></script>'
    return f'''<!doctype html><html lang="fa" dir="rtl"><head>
<meta name="theme-color" content="#080d1c">{BOOTSTRAP}
<link rel="stylesheet" href="{data_url(VARS,"text/css")}">
<link rel="stylesheet" href="{data_url(style or ".test-target { padding: 4px; }", "text/css")}">
<meta data-ajax-style-boundary></head>
<body class="{'auth-page' if kind == 'auth' else ''}">
<script>window.DevixaTheme?.syncBody();</script>
<nav id="menubar">منوی دویکسا<input id="theme_toggle" type="checkbox">
<button data-auth-theme-toggle>تغییر تم</button></nav>
<main class="test-target"><h1>{'ورود' if kind == 'auth' else 'پروفایل'}</h1></main>
{script}</body></html>'''


def run():
    count = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_EXECUTABLE', '/usr/bin/chromium'), headless=True, args=['--no-sandbox'])
        for width in (390, 1440):
            context = browser.new_context(viewport={'width':width,'height':800})
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            # about:blank has an opaque origin: simulate persistent storage without network.
            page.evaluate('''() => {
                const store = {theme:'light'};
                Object.defineProperty(window, 'localStorage', {configurable:true, value:{
                    getItem:k => store[k] || null, setItem:(k,v) => {store[k]=v},
                    removeItem:k => {delete store[k]}
                }});
            }''')
            page.set_content(document('theme'),wait_until='load')
            assert page.locator('html').get_attribute('data-theme') == 'light'
            assert page.locator('body').get_attribute('data-theme') == 'light'
            assert page.locator('body').evaluate('el=>el.classList.contains("light-theme")')
            count += 1

            # Run the actual theme module and its real change handler.
            page.add_script_tag(content=THEME_JS)
            page.locator('#theme_toggle').check()
            page.locator('#theme_toggle').uncheck()
            assert page.locator('html').get_attribute('data-theme') == 'dark'
            assert page.evaluate('localStorage.getItem("theme")') == 'dark'
            count += 1

            # Simulate navigation with a different body/template while storage persists.
            page.set_content(document('auth'),wait_until='load')
            assert page.locator('html').get_attribute('data-theme') == 'dark'
            assert page.locator('body').get_attribute('data-theme') == 'dark'
            page.add_script_tag(content=AUTH_JS)
            page.locator('[data-auth-theme-toggle]').click()
            assert page.locator('html').get_attribute('data-theme') == 'light'
            assert page.evaluate('localStorage.getItem("theme")') == 'light'
            count += 1

            # Exercise the actual AJAX stylesheet handoff and body replacement.
            # Inline CSS is deliberately changed to a new data: stylesheet.
            page.add_script_tag(content=JQUERY_JS)
            page.add_script_tag(content=AJAX_JS)
            page.wait_for_function('Boolean(window.DevixaAjaxForms)')
            next_html = document('theme',style='.test-target { padding: 12px; }')
            # Intercept only the transport; run the real AJAX reconciliation code.
            page.evaluate('''(nextHtml) => {
                const realAjax = jQuery.ajax;
                jQuery.ajax = function(options) {
                    const request = jQuery.Deferred();
                    request.abort = () => request.reject({}, 'abort');
                    queueMicrotask(() => request.resolve(nextHtml, 'success', {responseURL:'https://fixture.invalid/profile/'}));
                    return request;
                };
                window.DevixaAjaxForms.loadPage('https://fixture.invalid/profile/', {pushHistory:false});
            }''',next_html)
            page.wait_for_function('document.querySelector("main h1")?.textContent === "پروفایل" && document.body.dataset.theme === "light"',timeout=10000)
            assert page.locator('html').get_attribute('data-theme') == 'light'
            assert page.locator('meta[name="theme-color"]').get_attribute('content') == '#f5f7fe'
            assert page.locator('main').evaluate('el => getComputedStyle(el).visibility') == 'visible'
            page.wait_for_timeout(120)
            assert errors == [], errors
            count += 1
            context.close()
        browser.close()
    print(f'PASS: {count} offline Chromium frontend scenarios across two viewport widths; Django integration not tested.')


if __name__ == '__main__':
    run()
