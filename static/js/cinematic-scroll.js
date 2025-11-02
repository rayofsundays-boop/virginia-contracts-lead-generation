/**
 * Cinematic Scroll Experience
 * Inspired by Opus Agent - scroll-driven storytelling with GSAP & Lenis
 */

// Initialize Lenis smooth scroll
const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // easeOutExpo
    direction: 'vertical',
    smooth: true,
    smoothTouch: false,
    touchMultiplier: 2
});

// Lenis RAF loop
function raf(time) {
    lenis.raf(time);
    requestAnimationFrame(raf);
}
requestAnimationFrame(raf);

// Sync GSAP ScrollTrigger with Lenis
lenis.on('scroll', ScrollTrigger.update);

gsap.ticker.add((time) => {
    lenis.raf(time * 1000);
});

gsap.ticker.lagSmoothing(0);

// ============================================
// SCENE 1: Hero Scene - Logo + Headline Fade In
// ============================================
gsap.from('.hero-scene .hero-logo', {
    scrollTrigger: {
        trigger: '.hero-scene',
        start: 'top center',
        end: 'center center',
        scrub: 1,
        // markers: true // Uncomment for debugging
    },
    scale: 0.8,
    opacity: 0,
    y: 100,
    duration: 1.5,
    ease: 'power3.out'
});

gsap.from('.hero-scene .hero-headline', {
    scrollTrigger: {
        trigger: '.hero-scene',
        start: 'top center',
        end: 'center center',
        scrub: 1
    },
    opacity: 0,
    y: 80,
    duration: 1.5,
    ease: 'power3.out',
    stagger: 0.2
});

gsap.from('.hero-scene .hero-subtext', {
    scrollTrigger: {
        trigger: '.hero-scene',
        start: 'top center',
        end: 'center center',
        scrub: 1
    },
    opacity: 0,
    y: 60,
    duration: 1.5,
    delay: 0.3,
    ease: 'power3.out'
});

// Hero CTA buttons slide up
gsap.from('.hero-scene .cta-button', {
    scrollTrigger: {
        trigger: '.hero-scene',
        start: 'top center',
        end: 'center center',
        scrub: 1
    },
    opacity: 0,
    y: 40,
    duration: 1,
    stagger: 0.1,
    ease: 'back.out(1.7)'
});

// ============================================
// SCENE 2: Storytelling Scenes - Text + Image Panels
// ============================================
gsap.utils.toArray('.story-scene').forEach((scene, index) => {
    const isEven = index % 2 === 0;
    
    // Animate text panel
    gsap.from(scene.querySelector('.story-text'), {
        scrollTrigger: {
            trigger: scene,
            start: 'top 80%',
            end: 'top 30%',
            scrub: 1
        },
        x: isEven ? -100 : 100,
        opacity: 0,
        duration: 1.5,
        ease: 'power3.out'
    });
    
    // Animate image/video panel with parallax
    gsap.from(scene.querySelector('.story-media'), {
        scrollTrigger: {
            trigger: scene,
            start: 'top 80%',
            end: 'top 30%',
            scrub: 1
        },
        x: isEven ? 100 : -100,
        opacity: 0,
        scale: 0.9,
        duration: 1.5,
        ease: 'power3.out'
    });
    
    // Parallax effect for media
    gsap.to(scene.querySelector('.story-media'), {
        scrollTrigger: {
            trigger: scene,
            start: 'top bottom',
            end: 'bottom top',
            scrub: 2
        },
        y: -50,
        ease: 'none'
    });
    
    // Background color transition
    ScrollTrigger.create({
        trigger: scene,
        start: 'top center',
        end: 'bottom center',
        onEnter: () => scene.classList.add('active'),
        onLeave: () => scene.classList.remove('active'),
        onEnterBack: () => scene.classList.add('active'),
        onLeaveBack: () => scene.classList.remove('active')
    });
});

// ============================================
// SCENE 3: AI Agent Showcase - Animated Cards
// ============================================
gsap.utils.toArray('.ai-card').forEach((card, index) => {
    // Cards slide in from different directions with glow
    const directions = ['left', 'bottom', 'right'];
    const direction = directions[index % 3];
    const startPos = {
        left: { x: -150, y: 0 },
        bottom: { x: 0, y: 150 },
        right: { x: 150, y: 0 }
    };
    
    gsap.from(card, {
        scrollTrigger: {
            trigger: '.ai-showcase',
            start: 'top 70%',
            end: 'top 30%',
            scrub: 1
        },
        ...startPos[direction],
        opacity: 0,
        scale: 0.8,
        rotation: direction === 'left' ? -5 : direction === 'right' ? 5 : 0,
        duration: 1.5,
        delay: index * 0.1,
        ease: 'back.out(1.7)'
    });
    
    // Glow effect on scroll
    gsap.to(card, {
        scrollTrigger: {
            trigger: card,
            start: 'top 80%',
            end: 'top 50%',
            scrub: 1
        },
        boxShadow: '0 0 40px rgba(102, 126, 234, 0.6)',
        duration: 0.5
    });
    
    // 3D perspective tilt on hover (not scroll-based but adds interactivity)
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 10;
        const rotateY = (centerX - x) / 10;
        
        gsap.to(card, {
            rotateX: rotateX,
            rotateY: rotateY,
            duration: 0.3,
            ease: 'power2.out'
        });
    });
    
    card.addEventListener('mouseleave', () => {
        gsap.to(card, {
            rotateX: 0,
            rotateY: 0,
            duration: 0.5,
            ease: 'power2.out'
        });
    });
});

// ============================================
// SCENE 4: Statistics Counter Animation
// ============================================
gsap.utils.toArray('.stat-item').forEach((stat, index) => {
    const number = stat.querySelector('.stat-number');
    const target = parseInt(number.getAttribute('data-target'));
    
    gsap.from(stat, {
        scrollTrigger: {
            trigger: '.stats-section',
            start: 'top 80%',
            end: 'top 50%',
            scrub: 1
        },
        y: 50,
        opacity: 0,
        scale: 0.9,
        duration: 1,
        delay: index * 0.1,
        ease: 'back.out(1.7)'
    });
    
    // Counter animation
    ScrollTrigger.create({
        trigger: stat,
        start: 'top 80%',
        onEnter: () => {
            gsap.to({ val: 0 }, {
                val: target,
                duration: 2,
                ease: 'power2.out',
                onUpdate: function() {
                    number.textContent = Math.ceil(this.targets()[0].val);
                }
            });
        }
    });
});

// ============================================
// SCENE 5: Call-to-Action with Cinematic Lighting
// ============================================
gsap.from('.cta-scene .cta-content', {
    scrollTrigger: {
        trigger: '.cta-scene',
        start: 'top 70%',
        end: 'top 30%',
        scrub: 1
    },
    scale: 0.9,
    opacity: 0,
    y: 80,
    duration: 1.5,
    ease: 'power3.out'
});

// Cinematic light beam effect
gsap.to('.cta-scene .light-beam', {
    scrollTrigger: {
        trigger: '.cta-scene',
        start: 'top 70%',
        end: 'bottom top',
        scrub: 2
    },
    opacity: 0.8,
    scale: 1.2,
    rotation: 360,
    duration: 3,
    ease: 'none'
});

// Motion blur effect on CTA button
gsap.to('.cta-scene .cta-button-final', {
    scrollTrigger: {
        trigger: '.cta-scene',
        start: 'top 60%',
        end: 'top 40%',
        scrub: 1
    },
    scale: 1.05,
    duration: 0.5,
    ease: 'power2.inOut',
    yoyo: true,
    repeat: -1
});

// ============================================
// BACKGROUND TRANSITIONS - Dynamic Color Shifts
// ============================================
const scenes = [
    { trigger: '.hero-scene', colors: ['#1a0a2e', '#0f3460'] },
    { trigger: '.story-scene-1', colors: ['#0f3460', '#16213e'] },
    { trigger: '.story-scene-2', colors: ['#16213e', '#0f4c75'] },
    { trigger: '.ai-showcase', colors: ['#0f4c75', '#1b262c'] },
    { trigger: '.cta-scene', colors: ['#1b262c', '#0f0e17'] }
];

scenes.forEach((scene, index) => {
    ScrollTrigger.create({
        trigger: scene.trigger,
        start: 'top center',
        end: 'bottom center',
        onEnter: () => {
            gsap.to('body', {
                background: `linear-gradient(135deg, ${scene.colors[0]}, ${scene.colors[1]})`,
                duration: 1.5,
                ease: 'power2.inOut'
            });
        },
        onEnterBack: () => {
            gsap.to('body', {
                background: `linear-gradient(135deg, ${scene.colors[0]}, ${scene.colors[1]})`,
                duration: 1.5,
                ease: 'power2.inOut'
            });
        }
    });
});

// ============================================
// PARALLAX ELEMENTS - Floating Particles & Shapes
// ============================================
gsap.utils.toArray('.parallax-element').forEach((element) => {
    const speed = element.getAttribute('data-speed') || 0.5;
    
    gsap.to(element, {
        scrollTrigger: {
            trigger: element,
            start: 'top bottom',
            end: 'bottom top',
            scrub: 2
        },
        y: () => -window.innerHeight * speed,
        ease: 'none'
    });
});

// Floating geometric shapes animation
gsap.utils.toArray('.geometric-shape').forEach((shape, index) => {
    gsap.to(shape, {
        scrollTrigger: {
            trigger: 'body',
            start: 'top top',
            end: 'bottom bottom',
            scrub: 3
        },
        y: index % 2 === 0 ? -300 : 300,
        x: index % 2 === 0 ? 200 : -200,
        rotation: index * 120,
        ease: 'none'
    });
});

// ============================================
// SCROLL PROGRESS INDICATOR
// ============================================
gsap.to('.scroll-progress', {
    scrollTrigger: {
        trigger: 'body',
        start: 'top top',
        end: 'bottom bottom',
        scrub: 0.5
    },
    scaleY: 1,
    transformOrigin: 'top',
    ease: 'none'
});

// Update progress percentage
ScrollTrigger.create({
    trigger: 'body',
    start: 'top top',
    end: 'bottom bottom',
    onUpdate: (self) => {
        const progress = Math.round(self.progress * 100);
        const progressText = document.querySelector('.progress-text');
        if (progressText) {
            progressText.textContent = `${progress}%`;
        }
    }
});

// ============================================
// SECTION TIMELINE DOTS - Visual Navigation
// ============================================
const sections = document.querySelectorAll('[data-section]');
const dots = document.querySelectorAll('.timeline-dot');

sections.forEach((section, index) => {
    ScrollTrigger.create({
        trigger: section,
        start: 'top center',
        end: 'bottom center',
        onEnter: () => dots[index]?.classList.add('active'),
        onLeave: () => dots[index]?.classList.remove('active'),
        onEnterBack: () => dots[index]?.classList.add('active'),
        onLeaveBack: () => dots[index]?.classList.remove('active')
    });
});

// Click to scroll to section
dots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
        lenis.scrollTo(sections[index], {
            offset: 0,
            duration: 1.5,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t))
        });
    });
});

// ============================================
// PERFORMANCE OPTIMIZATIONS
// ============================================

// Use GPU acceleration for all animated elements
gsap.set(['.hero-scene', '.story-scene', '.ai-card', '.cta-scene'], {
    force3D: true,
    willChange: 'transform'
});

// Pause animations when tab is not visible
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        gsap.globalTimeline.pause();
    } else {
        gsap.globalTimeline.resume();
    }
});

// ============================================
// RESPONSIVE ADJUSTMENTS
// ============================================
const mm = gsap.matchMedia();

mm.add("(max-width: 768px)", () => {
    // Reduce animation complexity on mobile
    gsap.utils.toArray('.ai-card').forEach((card) => {
        gsap.set(card, { transform: 'none' });
    });
    
    // Simplify parallax on mobile
    gsap.utils.toArray('.parallax-element').forEach((element) => {
        gsap.set(element, { y: 0 });
    });
});

mm.add("(min-width: 769px)", () => {
    // Full animations on desktop
    console.log('Desktop animations enabled');
});

// ============================================
// PARTICLE SYSTEM (Canvas-based for performance)
// ============================================
const canvas = document.querySelector('.particles-canvas');
if (canvas) {
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const particles = [];
    const particleCount = 50;
    
    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 3 + 1;
            this.speedX = Math.random() * 0.5 - 0.25;
            this.speedY = Math.random() * 0.5 - 0.25;
            this.opacity = Math.random() * 0.5 + 0.3;
        }
        
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            
            if (this.x > canvas.width) this.x = 0;
            if (this.x < 0) this.x = canvas.width;
            if (this.y > canvas.height) this.y = 0;
            if (this.y < 0) this.y = canvas.height;
        }
        
        draw() {
            ctx.fillStyle = `rgba(102, 126, 234, ${this.opacity})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
    
    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });
        requestAnimationFrame(animateParticles);
    }
    
    animateParticles();
    
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

console.log('🎬 Cinematic scroll experience loaded');
