(() => {
    const copyButtons = document.querySelectorAll('[data-copy-button]');
    copyButtons.forEach((button) => {
        button.addEventListener('click', async () => {
            const value = button.dataset.copy || '';
            if (!value) return;
            try {
                await navigator.clipboard.writeText(value);
                const original = button.innerHTML;
                button.innerHTML = '<i class="fa-solid fa-check"></i>کپی شد';
                window.setTimeout(() => { button.innerHTML = original; }, 1600);
            } catch (_) {
                const temporary = document.createElement('textarea');
                temporary.value = value;
                temporary.style.position = 'fixed';
                temporary.style.opacity = '0';
                document.body.appendChild(temporary);
                temporary.select();
                document.execCommand('copy');
                temporary.remove();
            }
        });
    });

    const input = document.querySelector('[data-receipt-input]');
    const preview = document.querySelector('[data-receipt-preview]');
    if (!input || !preview) return;
    const image = preview.querySelector('[data-receipt-preview-image]');
    const name = preview.querySelector('[data-receipt-preview-name]');
    const dropzoneName = document.querySelector('[data-receipt-file-name]');
    let objectUrl = null;

    input.addEventListener('change', () => {
        const file = input.files && input.files[0];
        if (!file) {
            preview.hidden = true;
            return;
        }
        if (objectUrl) URL.revokeObjectURL(objectUrl);
        name.textContent = file.name;
        if (dropzoneName) dropzoneName.textContent = file.name;
        if (file.type.startsWith('image/')) {
            objectUrl = URL.createObjectURL(file);
            image.src = objectUrl;
            image.hidden = false;
        } else {
            image.removeAttribute('src');
            image.hidden = true;
        }
        preview.hidden = false;
    });
})();
