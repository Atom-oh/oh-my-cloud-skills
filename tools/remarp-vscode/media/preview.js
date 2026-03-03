// Webview script for Remarp Preview
(function() {
    const vscode = acquireVsCodeApi();

    // Handle messages from the extension
    window.addEventListener('message', event => {
        const message = event.data;

        switch (message.command) {
            case 'updateSlide':
                updateSlideContent(message.content);
                break;
            case 'navigateTo':
                // Could be used for programmatic navigation
                break;
        }
    });

    // Update the slide container with new content
    function updateSlideContent(html) {
        const container = document.querySelector('.slide');
        if (container) {
            container.innerHTML = html;
        }
    }

    // Navigation functions (called from inline onclick handlers in preview.ts)
    window.nextSlide = function() {
        vscode.postMessage({ command: 'nextSlide' });
    };

    window.prevSlide = function() {
        vscode.postMessage({ command: 'prevSlide' });
    };

    window.goToSlide = function(index) {
        vscode.postMessage({ command: 'navigateSlide', index: index });
    };

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        // Right arrow or Space -> next slide
        if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
            e.preventDefault();
            window.nextSlide();
        }
        // Left arrow -> previous slide
        else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
            e.preventDefault();
            window.prevSlide();
        }
        // Home -> first slide
        else if (e.key === 'Home') {
            e.preventDefault();
            window.goToSlide(0);
        }
    });

    // Touch/swipe support for mobile preview
    let touchStartX = 0;
    let touchEndX = 0;

    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    });

    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });

    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;

        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                // Swiped left -> next slide
                window.nextSlide();
            } else {
                // Swiped right -> previous slide
                window.prevSlide();
            }
        }
    }

    // Notify extension that webview is ready
    vscode.postMessage({ command: 'webviewReady' });
})();
