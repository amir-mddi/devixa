(() => {
    'use strict';

    const menubar = document.getElementById('menubar');
    const toggle = document.getElementById('theme_toggle');
    if (!toggle) return;

    const savedTheme = localStorage.getItem('theme');
    const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
    const shouldUseLight = savedTheme ? savedTheme === 'light' : prefersLight;

    function applyTheme(isLight) {
        const themeName = isLight ? 'light' : 'dark';
        document.body.classList.toggle('light-theme', isLight);
        document.body.dataset.theme = themeName;
        document.documentElement.dataset.theme = themeName;
        toggle.checked = isLight;
        if (menubar) menubar.classList.toggle('background', isLight);
        localStorage.setItem('theme', themeName);
        document.documentElement.style.colorScheme = themeName;
        const themeColor = document.querySelector('meta[name="theme-color"]');
        if (themeColor) themeColor.setAttribute('content', isLight ? '#f5f7ff' : '#070b14');
    }

    applyTheme(shouldUseLight);
    toggle.addEventListener('change', () => applyTheme(toggle.checked));
})();
