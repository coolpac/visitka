    // Contact button functionality
    document.addEventListener('DOMContentLoaded', function() {
        const contactButtons = document.querySelectorAll('.contact-button, .values-contact-button');
        
        contactButtons.forEach(button => {
            button.addEventListener('click', function() {
                const email = 'anna.anna.ivaschenko@gmail.com';
                window.location.href = `mailto:${email}?subject=Контакт с сайта-визитки`;
            });
        });

    // Hero slider
    const heroSlides = document.querySelectorAll('.hero-slide');
    const heroNextBtn = document.querySelector('.hero-slider__button[data-action="next"]');
    const heroPrevBtn = document.querySelector('.hero-slider__button[data-action="prev"]');
    let heroActiveIndex = 0;
    let heroSliderInterval;

    const setActiveHeroSlide = (index) => {
        heroSlides.forEach((slide, i) => {
            slide.classList.toggle('is-active', i === index);
        });
        heroActiveIndex = index;
    };

    const showNextHeroSlide = () => {
        const nextIndex = (heroActiveIndex + 1) % heroSlides.length;
        setActiveHeroSlide(nextIndex);
    };

    const showPrevHeroSlide = () => {
        const prevIndex = (heroActiveIndex - 1 + heroSlides.length) % heroSlides.length;
        setActiveHeroSlide(prevIndex);
    };

    const startHeroSlider = () => {
        if (heroSliderInterval) clearInterval(heroSliderInterval);
        heroSliderInterval = setInterval(showNextHeroSlide, 5000);
    };

    if (heroSlides.length > 0) {
        setActiveHeroSlide(0);
        startHeroSlider();
    }

    if (heroNextBtn) {
        heroNextBtn.addEventListener('click', () => {
            showNextHeroSlide();
            startHeroSlider();
        });
    }

    if (heroPrevBtn) {
        heroPrevBtn.addEventListener('click', () => {
            showPrevHeroSlide();
            startHeroSlider();
        });
    }

    // Smooth scroll for better UX
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Speaker slider
    const slides = document.querySelectorAll('.speaker-slide');
    const nextBtn = document.querySelector('.speaker-slider__button[data-action="next"]');
    const prevBtn = document.querySelector('.speaker-slider__button[data-action="prev"]');
    let activeIndex = 0;
    let sliderInterval;

    const setActiveSlide = (index) => {
        slides.forEach((slide, i) => {
            slide.classList.toggle('is-active', i === index);
        });
        activeIndex = index;
    };

    const showNextSlide = () => {
        const nextIndex = (activeIndex + 1) % slides.length;
        setActiveSlide(nextIndex);
    };

    const showPrevSlide = () => {
        const prevIndex = (activeIndex - 1 + slides.length) % slides.length;
        setActiveSlide(prevIndex);
    };

    const startSlider = () => {
        if (sliderInterval) clearInterval(sliderInterval);
        sliderInterval = setInterval(showNextSlide, 5000);
    };

    if (slides.length > 0) {
        setActiveSlide(0);
        startSlider();
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            showNextSlide();
            startSlider();
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            showPrevSlide();
            startSlider();
        });
    }
});

