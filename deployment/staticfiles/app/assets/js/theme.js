(() => {
    'use strict';

    const menubar = document.getElementById('menubar');
    const toggle = document.getElementById('theme_toggle');
    if (!toggle) return;

    const savedTheme = localStorage.getItem('theme');
    const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
    const shouldUseLight = savedTheme ? savedTheme === 'light' : prefersLight;

    function applyTheme(isLight) {
        document.body.classList.toggle('light-theme', isLight);
        toggle.checked = isLight;
        if (menubar) menubar.classList.toggle('background', isLight);
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
        document.documentElement.style.colorScheme = isLight ? 'light' : 'dark';
    }

    applyTheme(shouldUseLight);
    toggle.addEventListener('change', () => applyTheme(toggle.checked));
})();
