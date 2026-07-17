(() => {
    "use strict";

    const initFaq = () => {
        const faqGroups = document.querySelectorAll("[data-home-faq]");

        faqGroups.forEach((group) => {
            const items = Array.from(group.querySelectorAll("details.home-faq-v3__item"));

            items.forEach((item) => {
                item.addEventListener("toggle", () => {
                    if (!item.open) {
                        return;
                    }

                    items.forEach((otherItem) => {
                        if (otherItem !== item && otherItem.open) {
                            otherItem.open = false;
                        }
                    });
                });
            });
        });
    };

    const initTestimonials = () => {
        const viewport = document.querySelector("[data-home-testimonials-viewport]");
        const track = document.querySelector("[data-home-testimonials-track]");
        const prevButton = document.querySelector("[data-home-testimonial-prev]");
        const nextButton = document.querySelector("[data-home-testimonial-next]");

        if (!viewport || !track || !prevButton || !nextButton) {
            return;
        }

        const cards = Array.from(track.querySelectorAll(".home-testimonial-card-v4"));

        if (!cards.length) {
            prevButton.disabled = true;
            nextButton.disabled = true;
            return;
        }

        let pageIndex = 0;

        const getGap = () => {
            const styles = window.getComputedStyle(track);
            return Number.parseFloat(styles.columnGap || styles.gap || "0") || 0;
        };

        const getVisibleCount = () => {
            const firstCard = cards[0];
            if (!firstCard) {
                return 1;
            }

            const cardWidth = firstCard.getBoundingClientRect().width;
            if (!cardWidth) {
                return 1;
            }

            const gap = getGap();
            return Math.max(1, Math.floor((viewport.clientWidth + gap) / (cardWidth + gap)));
        };

        const getMaxPage = () => {
            const visibleCount = getVisibleCount();
            return Math.max(0, Math.ceil(cards.length / visibleCount) - 1);
        };

        const clampPageIndex = () => {
            pageIndex = Math.min(Math.max(pageIndex, 0), getMaxPage());
        };

        const scrollToPage = (behavior = "smooth") => {
            clampPageIndex();
            const visibleCount = getVisibleCount();
            const cardWidth = cards[0]?.getBoundingClientRect().width || 0;
            const pageWidth = visibleCount * (cardWidth + getGap());
            const maximumOffset = Math.max(0, track.scrollWidth - track.clientWidth);
            const requestedOffset = Math.min(pageIndex * pageWidth, maximumOffset);
            const isRtl = window.getComputedStyle(track).direction === "rtl";

            track.scrollTo({
                left: isRtl ? -requestedOffset : requestedOffset,
                behavior,
            });

            prevButton.disabled = pageIndex === 0;
            nextButton.disabled = pageIndex >= getMaxPage();
        };

        prevButton.addEventListener("click", () => {
            pageIndex -= 1;
            scrollToPage();
        });

        nextButton.addEventListener("click", () => {
            pageIndex += 1;
            scrollToPage();
        });

        window.addEventListener("resize", () => {
            scrollToPage("auto");
        });

        scrollToPage("auto");
    };

    initFaq();
    initTestimonials();
})();
