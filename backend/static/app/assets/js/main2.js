(() => {
    'use strict';

    const track = document.querySelector('.student_reviews .carousel_wrapper .review_cards');
    const prevBtn = document.getElementById('prevBtn2');
    const nextBtn = document.getElementById('nextBtn2');
    if (!track || !prevBtn || !nextBtn) return;

    const cards = [...track.querySelectorAll('.student_reviews .carousel_wrapper .review_cards .card')];
    if (!cards.length) return;

    let currentIndex = 0;

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
        track.style.transform = `translateX(${currentIndex * getCardWidth()}px)`;
    }

    nextBtn.addEventListener('click', (event) => {
        event.preventDefault();
        if (currentIndex < cards.length - getVisibleCount()) {
            currentIndex += 1;
            updateSlider();
        }
    });

    prevBtn.addEventListener('click', (event) => {
        event.preventDefault();
        if (currentIndex > 0) {
            currentIndex -= 1;
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
})();
