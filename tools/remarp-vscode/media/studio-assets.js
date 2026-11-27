/* Resolve only the finite image bundle; never request workspace resources from the host. */
(() => {
    'use strict';
    const resources = window.__remarpStudioAssets || {};
    delete window.__remarpStudioAssets;
    const empty = 'data:application/octet-stream;base64,';
    const warned = new Set();
    function resolve(value) {
        const url = String(value);
        if (/^(?:[a-z][\w+.-]*:|\/\/|#)/i.test(url)) return url;
        let key;
        try {
            const parsed = new URL(url, 'https://remarp-studio.invalid/');
            key = decodeURIComponent(parsed.pathname).replace(/^\//, '');
            if (Object.prototype.hasOwnProperty.call(resources, key)) return resources[key] + parsed.hash;
        } catch { /* Invalid URLs never fall back to the parent webview resource origin. */ }
        if (warned.size < 12 && !warned.has(url)) {
            warned.add(url);
            console.warn('Studio optional image is unavailable in the isolated bundle:', url.slice(0, 200));
        }
        return empty;
    }
    const descriptor = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
    Object.defineProperty(HTMLImageElement.prototype, 'src', {
        ...descriptor,
        set(value) { descriptor.set.call(this, resolve(value)); }
    });
    const setAttribute = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function(name, value) {
        if (this instanceof HTMLImageElement && String(name).toLowerCase() === 'src') value = resolve(value);
        return setAttribute.call(this, name, value);
    };
})();
