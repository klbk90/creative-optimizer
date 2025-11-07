/**
 * Landing Page Redirect Script
 * Handles countdown timer and automatic redirect to Telegram
 */

class LandingRedirect {
    constructor(redirectUrl, delay = 3) {
        this.redirectUrl = redirectUrl;
        this.delay = delay;
        this.remaining = delay;
        this.interval = null;
        this.progressBar = null;
        this.timerElement = null;
    }

    init() {
        this.findElements();
        this.startCountdown();
        this.trackPageView();
    }

    findElements() {
        this.timerElement = document.querySelector('.redirect-timer');
        this.progressBar = document.querySelector('.progress-bar');
    }

    startCountdown() {
        // Update immediately
        this.updateUI();

        // Start interval
        this.interval = setInterval(() => {
            this.remaining -= 0.1;

            if (this.remaining <= 0) {
                this.redirect();
            } else {
                this.updateUI();
            }
        }, 100); // Update every 100ms for smooth progress bar
    }

    updateUI() {
        // Update timer text
        if (this.timerElement) {
            const seconds = Math.ceil(this.remaining);
            this.timerElement.textContent = seconds;
        }

        // Update progress bar
        if (this.progressBar) {
            const progress = ((this.delay - this.remaining) / this.delay) * 100;
            this.progressBar.style.width = `${progress}%`;
        }
    }

    redirect() {
        clearInterval(this.interval);

        // Track redirect event
        this.trackRedirect();

        // Redirect
        window.location.href = this.redirectUrl;
    }

    trackPageView() {
        // Track that user viewed the landing page
        if (window.landingConfig && window.landingConfig.utm_id) {
            // This will be tracked by server-side when page loads
            console.log('Landing page viewed:', window.landingConfig.utm_id);
        }
    }

    trackRedirect() {
        // Track redirect click
        if (window.landingConfig && window.landingConfig.utm_id) {
            console.log('Redirecting to Telegram:', window.landingConfig.utm_id);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const config = window.landingConfig || {};
    const redirectUrl = config.redirect_url || 'https://t.me/your_bot';
    const delay = config.redirect_delay || 3;

    const redirect = new LandingRedirect(redirectUrl, delay);
    redirect.init();
});

// Add particles animation (optional)
function createParticles() {
    const particlesContainer = document.querySelector('.particles');
    if (!particlesContainer) return;

    const particleCount = 20;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';

        // Random size
        const size = Math.random() * 10 + 5;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;

        // Random starting position
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;

        // Random animation delay
        particle.style.animationDelay = `${Math.random() * 10}s`;
        particle.style.animationDuration = `${Math.random() * 10 + 10}s`;

        particlesContainer.appendChild(particle);
    }
}

// Create particles on load
document.addEventListener('DOMContentLoaded', () => {
    createParticles();
});

// Prevent accidental navigation away
window.addEventListener('beforeunload', (e) => {
    // Don't show prompt if we're redirecting
    if (window.isRedirecting) return;

    // Optional: show confirmation if user tries to leave
    // Uncomment if you want to prevent accidental closes
    // e.preventDefault();
    // e.returnValue = '';
});
