/* Renderer observations only. This sandbox never receives a VS Code API. */
(() => {
    'use strict';
    const config = window.__remarpStudio;
    if (!config) return;
    const params = new URLSearchParams(location.search), thumbnail = params.has('studioThumbnail');
    let mode = thumbnail ? 'design' : 'play', pending = false, designSidebar;
    const revealAdvance = new Map();
    const runtime = () => typeof deck !== 'undefined' ? deck : null;
    const slides = () => Array.from(runtime()?.slides || document.querySelectorAll('.slide-deck > .slide'));
    const active = () => slides().findIndex(s => s.classList.contains('active'));
    function configure() {
        const view = runtime();
        if (mode === 'design' && view?.sidebar && designSidebar === undefined) {
            designSidebar = view.sidebarVisible;
            view.hideSidebar(); // the Studio shell already owns navigation
        } else if (mode === 'play' && designSidebar !== undefined) {
            if (designSidebar) view?.showSidebar();
            designSidebar = undefined;
        }
        const slide = slides()[active()];
        if (!slide) return;
        document.documentElement.classList.toggle('studio-design', mode === 'design');
        if (mode === 'design' && typeof slide.__canvasStep === 'function' && !revealAdvance.has(slide)) {
            // The Canvas runtime accepts only the strings 'next' and 'prev', and the slide states its own
            // last step. Walk to it once; Play walks back the same distance.
            const last = Number(slide.dataset.canvasMaxStep) || 0;
            for (let n = 0; n < last; n++) slide.__canvasStep('next');
            revealAdvance.set(slide, last);
        }
    }
    const style = document.createElement('style');
    style.textContent = '.studio-design .fragment{opacity:1!important;visibility:visible!important}.studio-design .nav-hint,.studio-design .slide-counter{visibility:hidden}';
    document.head.append(style);
    function observe() {
        pending = false;
        if (thumbnail) return;
        const index = active(), slide = slides()[index];
        if (!slide) return;
        const elements = Array.from(slide.querySelectorAll('[data-remarp-id]'));
        const bounds = [];
        for (const node of config.nodes.filter(n => n.slide === index)) {
            const element = elements.find(e => e.dataset.remarpId === node.renderId);
            if (!element) continue;
            const rect = (node.geometry ? element.querySelector('canvas') : element)?.getBoundingClientRect();
            if (!rect || !rect.width || !rect.height) continue;
            if (node.geometry) {
                const g = node.geometry, scale = rect.width / g.canvasWidth;
                bounds.push({ id: node.id, x: rect.x + (g.x - (g.centered ? g.width / 2 : 0)) * scale,
                    y: rect.y + (g.y - (g.centered ? g.height / 2 : 0)) * scale,
                    width: g.width * scale, height: g.height * scale, canvasScale: scale });
            } else {
                bounds.push({ id: node.id, x: rect.x, y: rect.y, width: rect.width, height: rect.height });
            }
        }
        const deckElement = document.querySelector('.slide-deck');
        parent.postMessage({ type: 'studio-observation', generation: config.generation, slide: index, bounds,
            dimensions: { width: deckElement?.offsetWidth || 1920, height: deckElement?.offsetHeight || 1080 } }, '*');
    }
    function schedule() { if (!pending) { pending = true; requestAnimationFrame(() => { configure(); observe(); }); } }
    window.addEventListener('message', event => {
        if (event.source !== parent || thumbnail) return;
        const data = event.data;
        if (!data || data.type !== 'studio-view' || data.generation !== config.generation) return;
        const view = runtime();
        if (Number.isInteger(data.slide) && data.slide >= 0 && data.slide < slides().length && active() !== data.slide) {
            // Design selection must not depend on an in-flight presentation
            // transition (which temporarily leaves no active slide).
            if (data.mode === 'design') view?.showSlide(data.slide, false);
            else view?.goTo(data.slide);
        }
        if (data.mode === 'play' && mode === 'design') {
            for (const [slide, count] of revealAdvance) {
                for (let n = 0; n < count; n++) slide.__canvasStep?.('prev');
            }
            revealAdvance.clear();
        }
        if (data.mode === 'design' || data.mode === 'play') mode = data.mode;
        configure(); schedule();
    });
    const startup = () => {
        if (thumbnail) {
            runtime()?.showSlide(Number(params.get('studioSlide')) || 0, false);
            configure();
        }
        new ResizeObserver(schedule).observe(document.body);
        new MutationObserver(schedule).observe(document.querySelector('.slide-deck') || document.body,
            { attributes: true, childList: true, subtree: true });
        window.addEventListener('resize', schedule);
        document.fonts?.ready.then(schedule);
        schedule();
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', startup, { once: true }); else startup();
})();
