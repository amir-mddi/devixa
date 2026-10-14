(() => {
  'use strict';

  const root = document.querySelector('.dev-services');
  if (!root || root.dataset.initialized === 'true') return;
  root.dataset.initialized = 'true';

  // Choosing a service preselects the category while native anchor navigation
  // remains responsible for reaching the request form.
  const category = root.querySelector('#dev-services-form [name="category"]');
  if (!category) return;

  const validChoices = new Set(Array.from(category.options, (option) => option.value));
  root.querySelectorAll('[data-service-choice]').forEach((link) => {
    link.addEventListener('click', () => {
      const choice = link.dataset.serviceChoice;
      if (!validChoices.has(choice)) return;
      category.value = choice;
      category.dispatchEvent(new Event('change', { bubbles: true }));
    });
  });
})();
