(() => {
    'use strict';

    const navMenu = document.getElementById('navmenu');

    window.respo = function respo() {
        if (!navMenu) return;
        navMenu.classList.toggle('responsive');
    };

    document.addEventListener('click', (event) => {
        if (!navMenu || !navMenu.classList.contains('responsive')) return;
        const isMenuClick = event.target.closest('#navmenu');
        const isBarsClick = event.target.closest('.bars');
        if (!isMenuClick && !isBarsClick) navMenu.classList.remove('responsive');
    });

    const track = document.querySelector('.testimonial_track');
    const cards = track ? [...track.querySelectorAll('.testimonial_card')] : [];
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    let currentIndex = 0;

    if (track && cards.length && prevBtn && nextBtn) {
        function getVisibleCount() {
            const width = track.parentElement.offsetWidth;
            if (width >= 1024) return 3;
            if (width >= 640) return 2;
            return 1;
        }

        function updateCardWidths() {
            const visibleCount = getVisibleCount();
            const gap = 24;
            const totalGaps = (visibleCount - 1) * gap;
            const cardWidth = (track.parentElement.offsetWidth - totalGaps) / visibleCount;
            cards.forEach((card) => {
                card.style.width = `${cardWidth}px`;
            });
        }

        function getCardWidth() {
            return (cards[0]?.offsetWidth || 0) + 24;
        }

        function updateSlider() {
            track.style.transform = `translateX(${currentIndex * getCardWidth() * -1}px)`;
        }

        function getMaxIndex() {
            return -(cards.length - getVisibleCount());
        }

        nextBtn.addEventListener('click', (event) => {
            event.preventDefault();
            if (currentIndex > getMaxIndex()) {
                currentIndex -= 1;
                updateSlider();
            }
        });

        prevBtn.addEventListener('click', (event) => {
            event.preventDefault();
            if (currentIndex < 0) {
                currentIndex += 1;
                updateSlider();
            }
        });

        window.addEventListener('resize', () => {
            currentIndex = 0;
            updateCardWidths();
            updateSlider();
        });

        updateCardWidths();
        updateSlider();
    }

    const firstChip = document.querySelector('.course_section .course_hero .category_chips .chips a');
    if (firstChip) {
        firstChip.addEventListener('click', (event) => event.preventDefault());
    }
})();
