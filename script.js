document.addEventListener('DOMContentLoaded', function() {
    // Lazy loading with Intersection Observer
    const lazyLoadImages = () => {
        const imageObserverConfig = {
            root: null,
            rootMargin: '50px',
            threshold: 0.01
        };

        const imageObserverCallback = (entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.dataset.src;
                    const parent = img.closest('.skeleton-loader');
                    
                    const loadImage = () => {
                        if (src) {
                            const tempImg = new Image();
                            
                            tempImg.onload = () => {
                                img.src = src;
                                requestAnimationFrame(() => {
                                    img.classList.add('loaded');
                                    img.classList.remove('lazy');
                                    
                                    if (parent) {
                                        setTimeout(() => {
                                            parent.classList.remove('skeleton-loader');
                                        }, 400);
                                    }
                                });
                            };
                            
                            tempImg.onerror = () => {
                                console.warn('Failed to load image:', src);
                                img.src = src;
                                if (parent) {
                                    parent.classList.remove('skeleton-loader');
                                }
                            };
                            
                            tempImg.src = src;
                        }
                        observer.unobserve(img);
                    };
                    
                    if ('requestIdleCallback' in window) {
                        requestIdleCallback(loadImage, { timeout: 2000 });
                    } else {
                        setTimeout(loadImage, 0);
                    }
                }
            });
        };

        const imageObserver = new IntersectionObserver(imageObserverCallback, imageObserverConfig);
        const lazyImages = document.querySelectorAll('img.lazy');
        lazyImages.forEach(img => imageObserver.observe(img));
    };

    if ('IntersectionObserver' in window) {
        lazyLoadImages();
    } else {
        document.querySelectorAll('img.lazy').forEach(img => {
            if (img.dataset.src) {
                img.src = img.dataset.src;
                img.classList.add('loaded');
                img.classList.remove('lazy');
            }
        });
    }

    // Contact button functionality
    const contactButtons = document.querySelectorAll('.contact-button, .values-contact-button');
    
    contactButtons.forEach(button => {
        button.addEventListener('click', function() {
            const email = 'anna.anna.ivaschenko@gmail.com';
            window.location.href = `mailto:${email}?subject=Контакт с сайта-визитки`;
        });
    });

    // Hero slider
    const heroSlides = document.querySelectorAll('.hero-slide');
    let heroActiveIndex = 0;
    let heroSliderInterval;

    const setActiveHeroSlide = (index) => {
        heroSlides.forEach((slide, i) => {
            if (i === index) {
                slide.style.visibility = 'visible';
                slide.style.zIndex = '2';
                requestAnimationFrame(() => {
                    slide.classList.add('is-active');
                });
            } else {
                slide.classList.remove('is-active');
                setTimeout(() => {
                    slide.style.visibility = 'hidden';
                    slide.style.zIndex = '0';
                }, 1000);
            }
        });
        heroActiveIndex = index;
    };

    const showNextHeroSlide = () => {
        const nextIndex = (heroActiveIndex + 1) % heroSlides.length;
        setActiveHeroSlide(nextIndex);
    };

    const startHeroSlider = () => {
        if (heroSliderInterval) clearInterval(heroSliderInterval);
        heroSliderInterval = setInterval(showNextHeroSlide, 5000);
    };

    if (heroSlides.length > 0) {
        heroSlides[0].style.visibility = 'visible';
        heroSlides[0].classList.add('is-active');
        startHeroSlider();
        
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                if (heroSliderInterval) clearInterval(heroSliderInterval);
            } else {
                startHeroSlider();
            }
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

