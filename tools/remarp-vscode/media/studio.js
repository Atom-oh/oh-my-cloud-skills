/* Controlled editor shell. Authored iframe messages can report geometry, never edits. */
(() => {
    'use strict';
    const api = acquireVsCodeApi(), $ = id => document.getElementById(id), frame = $('preview');
    const saved = api.getState() || {};
    let manifest, generation, ready = false, slideIndex = saved.slide || 0, selected, mode = saved.mode || 'design';
    let scale = .4, dimensions = { width:1920, height:1080 }, bounds = [], proposalId;
    let draftDirty = false, draftGeneration, dragging;
    $('zoom').value = saved.zoom || 'fit';
    const slide = () => manifest?.slides[slideIndex];
    const node = () => slide()?.nodes.find(n => n.id === selected);
    const persist = () => api.setState({ slide:slideIndex, mode, zoom:$('zoom').value });
    function send(type, extra = {}) { api.postMessage({ type, generation, slide:slide()?.id, node:selected, ...extra }); }
    function edit(operation, value, property) { if (ready) send('edit', { operation, value, property }); }
    function notice(message) { $('diagnostics').textContent = message; $('diagnostics').hidden = false; }
    function status(value, message) {
        ready = value; $('status').textContent = message; $('status').classList.toggle('stale', !ready);
        $('fields').querySelectorAll('input,textarea,select,button').forEach(e => e.disabled = !ready);
        $('settings').querySelectorAll('select').forEach(e => e.disabled = !ready);
        for (const id of ['copy','issue','undo','redo']) $(id).disabled = !ready;
        $('source').disabled = !ready;
        $('propose').disabled = !ready || (draftDirty && draftGeneration !== generation);
        overlay();
    }
    function view() {
        frame.contentWindow?.postMessage({ type:'studio-view', generation, slide:slideIndex, mode }, '*');
        $('design').setAttribute('aria-pressed', String(mode === 'design')); $('play').setAttribute('aria-pressed', String(mode === 'play'));
        frame.style.pointerEvents = mode === 'play' ? 'auto' : 'none';
        persist(); overlay();
    }
    function zoom() {
        const viewport = $('viewport');
        scale = $('zoom').value === 'fit' ? Math.max(.05, Math.min((viewport.clientWidth - 44) / dimensions.width, (viewport.clientHeight - 44) / dimensions.height)) : Number($('zoom').value);
        $('stage').style.width = dimensions.width * scale + 'px'; $('stage').style.height = dimensions.height * scale + 'px';
        frame.style.width = dimensions.width + 'px'; frame.style.height = dimensions.height + 'px'; frame.style.transform = `scale(${scale})`;
        document.querySelectorAll('.thumbnail').forEach(t => {
            const f = t.firstElementChild;
            f.style.width = dimensions.width + 'px'; f.style.height = dimensions.height + 'px'; f.style.transform = `scale(${t.clientWidth / dimensions.width})`;
            t.style.height = dimensions.height * t.clientWidth / dimensions.width + 'px';
        });
        overlay(); persist();
    }
    function button(text, action, parent, className) {
        const b = document.createElement('button'); b.textContent = text;
        if (className) b.className = className;
        b.addEventListener('click', action); parent.append(b); return b;
    }
    function field(label, value, change, options = {}) {
        const wrap = document.createElement('label'); wrap.className = 'field';
        const caption = document.createElement('span'); caption.textContent = label; wrap.append(caption);
        const input = document.createElement(options.multiline ? 'textarea' : 'input'); input.value = String(value ?? '');
        input.disabled = !ready; if (options.number) { input.type = 'number'; input.min = '0'; input.max = '10000'; }
        // Change commits after IME composition, not on every keystroke.
        input.addEventListener('change', () => change(options.number ? Number(input.value) : input.value)); wrap.append(input);
        $('fields').append(wrap); return input;
    }
    function inspector() {
        const s = slide(), n = node(); $('fields').replaceChildren(); $('settings').replaceChildren(); $('layers').replaceChildren();
        if (!s) return;
        $('owner').textContent = `${s.file} · ${s.type} · ${n?.label || 'Slide source'}`;
        for (const item of s.nodes) {
            const b = button(item.label, () => { selected = item.id; inspector(); overlay(); }, $('layers'), 'layer');
            b.classList.toggle('selected', item.id === selected);
        }
        if (n?.text) field(n.geometry ? 'Canvas label' : 'Text / Markdown', n.text.value, value => edit('text', value));
        if (n?.body) field('Card body / Markdown', n.body.value, value => edit('body', value), { multiline:true });
        if (n?.geometry) {
            const inputs = {}, g = n.geometry;
            for (const key of ['x','y','width','height']) inputs[key] = field(key, g[key], () => {}, { number:true });
            const b = button('Apply geometry', () => edit('geometry', Object.fromEntries(Object.entries(inputs).map(([k,e]) => [k,Number(e.value)]))), $('fields')); b.disabled = !ready;
            if (n.step || n.lineEnd) field('Reveal step', n.step?.value || 0, value => edit('step', value), { number:true });
        }
        if (n?.cssTarget && s.cssEditable) {
            for (const property of ['color','font-size','font-weight','padding','margin-bottom','border-radius']) {
                const current = s.css?.targets[n.cssTarget]?.properties[property]?.value || '';
                field(property + ' (local override)', current, value => edit('style', value || null, property));
            }
            const info = document.createElement('small'); info.textContent = 'Blank removes an authored override and inherits the theme. Flow elements cannot be freely positioned.'; $('fields').append(info);
        }
        if (!n) { const info = document.createElement('p'); info.textContent = 'Select a layer or click an editable element. Other content remains source-only.'; $('fields').append(info); }
        const values = { fit:['auto','shrink','off'], columns:['1','2','3','4'], layout:['two-column','three-column','grid-2x2','grid-2x3','grid-3x2','grid-3x3'] };
        for (const [property, choices] of Object.entries(values)) {
            const label = document.createElement('label'); label.className = 'field'; label.textContent = property;
            const input = document.createElement('select'), inherited = document.createElement('option'); inherited.value = ''; inherited.textContent = 'Inherited / unchanged'; input.append(inherited);
            for (const value of choices) { const o = document.createElement('option'); o.value = value; o.textContent = value; input.append(o); }
            input.value = String(s.directives[property]?.value || ''); input.disabled = !ready || s.directives[property] === null;
            input.addEventListener('change', () => { if (input.value) edit('directive', input.value, property); }); label.append(input); $('settings').append(label);
        }
    }
    function navigation() {
        $('slides').replaceChildren();
        for (const [index, s] of manifest.slides.entries()) {
            const b = button('', () => {
                if (draftDirty && !confirm('Discard the current source draft and select another slide?')) return;
                slideIndex = index; selected = undefined; draftDirty = false; bounds = [];
                $('proposal').value = s.source; draftGeneration = generation;
                navigation(); inspector(); view();
            }, $('slides'), 'slide-item');
            b.classList.toggle('selected', index === slideIndex); b.setAttribute('aria-label', `${index + 1}. ${s.title}`);
            // A bounded window of real renderer thumbnails, not a second renderer.
            if (Math.abs(index - slideIndex) <= 2) {
                const t = document.createElement('span'); t.className = 'thumbnail';
                const f = document.createElement('iframe'); f.title = `Thumbnail: ${s.title}`; f.sandbox = 'allow-scripts'; f.tabIndex = -1; f.loading = 'lazy';
                f.src = frame.src + (frame.src.includes('?') ? '&' : '?') + `studioThumbnail=1&studioSlide=${index}`; t.append(f); b.append(t);
            }
            const title = document.createElement('span'); title.className = 'slide-label'; title.textContent = `${index + 1}. ${s.title}`; b.append(title);
        }
        requestAnimationFrame(zoom);
    }
    function overlay() {
        if (dragging) return;
        $('overlay').replaceChildren(); if (mode !== 'design') return;
        for (const rect of bounds) {
            const n = slide()?.nodes.find(n => n.id === rect.id); if (!n) continue;
            const b = button('', () => { selected = n.id; inspector(); overlay(); }, $('overlay'), 'hit');
            b.setAttribute('aria-label', `Select ${n.label}`); b.disabled = !ready; b.classList.toggle('selected', n.id === selected);
            Object.assign(b.style, { left:rect.x * scale + 'px', top:rect.y * scale + 'px', width:rect.width * scale + 'px', height:rect.height * scale + 'px' });
            if (n.geometry && ready) {
                b.addEventListener('pointerdown', e => drag(e, n, rect, b, false));
                if (selected === n.id) { const h = document.createElement('span'); h.className = 'handle'; h.setAttribute('aria-hidden','true'); b.append(h); h.addEventListener('pointerdown', e => { e.stopPropagation(); drag(e,n,rect,b,true); }); }
            }
        }
    }
    function drag(event, n, rect, element, resize) {
        if (event.button !== 0 || !rect.canvasScale || !ready) return;
        event.preventDefault(); selected = n.id; inspector();
        element.setPointerCapture(event.pointerId);
        dragging = { x:event.clientX, y:event.clientY, node:n, rect, element, resize, value:{ ...n.geometry }, moved:false };
        const move = e => {
            if (!dragging) return;
            const dx = (e.clientX - dragging.x) / (scale * rect.canvasScale), dy = (e.clientY - dragging.y) / (scale * rect.canvasScale), g = n.geometry;
            let x = g.x, y = g.y, width = g.width, height = g.height;
            if (resize) {
                width = Math.max(1,Math.round(g.width + dx)); height = n.kind === 'icon' ? width : Math.max(1,Math.round(g.height + dy));
            } else { x = Math.round(g.x + dx); y = Math.round(g.y + dy); }
            const value = { x,y,width,height }; dragging.value = value; dragging.moved = Math.abs(dx) + Math.abs(dy) > 1;
            Object.assign(element.style, { left:(rect.x + (x-g.x-(g.centered?(width-g.width)/2:0))*rect.canvasScale)*scale+'px', top:(rect.y+(y-g.y-(g.centered?(height-g.height)/2:0))*rect.canvasScale)*scale+'px', width:width*rect.canvasScale*scale+'px',height:height*rect.canvasScale*scale+'px' });
        };
        const finish = e => {
            const gesture = dragging; dragging = undefined;
            element.removeEventListener('pointermove', move); element.removeEventListener('pointerup', finish); element.removeEventListener('pointercancel', cancel);
            document.removeEventListener('keydown', escape); if (element.hasPointerCapture(event.pointerId)) element.releasePointerCapture(event.pointerId);
            if (e && gesture?.moved && ready) edit('geometry', gesture.value); overlay();
        };
        const cancel = () => finish(null), escape = e => { if (e.key === 'Escape') { e.preventDefault(); cancel(); } };
        element.addEventListener('pointermove', move); element.addEventListener('pointerup', finish); element.addEventListener('pointercancel', cancel); document.addEventListener('keydown', escape);
    }
    window.addEventListener('message', event => {
        const data = event.data; if (!data || typeof data !== 'object') return;
        if (event.source === frame.contentWindow) {
            // No type from this frame can call api.postMessage or alter source state.
            if (data.type !== 'studio-observation' || data.generation !== generation || !manifest) return;
            if (mode === 'play' && Number.isInteger(data.slide) && manifest.slides[data.slide] && data.slide !== slideIndex) {
                slideIndex = data.slide; selected = undefined; draftDirty = false; $('proposal').value = slide().source; navigation(); inspector(); persist();
            }
            if (data.slide !== slideIndex || !Array.isArray(data.bounds)) return;
            bounds = data.bounds.slice(0,2000).filter(b => b && typeof b.id === 'string' && ['x','y','width','height'].every(k => Number.isFinite(b[k]) && Math.abs(b[k]) < 100000) && b.width > 0 && b.height > 0);
            if (data.dimensions && ['width','height'].every(k => Number.isFinite(data.dimensions[k]) && data.dimensions[k] >= 100 && data.dimensions[k] <= 10000)) dimensions = data.dimensions;
            zoom(); return;
        }
        // Host messages come from this window (tests) or from the parent frame: VS Code forwards a webview
        // message through its outer page, so the sender is window.parent. Any other frame, such as one an
        // authored island opens inside the sandboxed preview, is not the host.
        if (event.source && event.source !== window && event.source !== window.parent) return;
        if (data.type === 'compiled' || data.type === 'candidate') {
            const old = slide(); manifest = data.manifest; generation = data.generation;
            if (!manifest || manifest.version !== 1 || !manifest.slides.length) return;
            const same = old ? manifest.slides.map((s,i) => ({s,i})).filter(({s}) => s.file === old.file && s.title === old.title) : [];
            slideIndex = same.length === 1 ? same[0].i : Math.min(slideIndex,manifest.slides.length-1);
            selected = undefined; bounds = []; proposalId = data.proposalId; $('candidate').hidden = !proposalId;
            if (!draftDirty) { $('proposal').value = slide().source; draftGeneration = generation; }
            else if (draftGeneration !== generation) notice('Source changed while a draft was open. Reset the draft from current source before proposing again.');
            frame.src = data.frameUrl;
            navigation(); inspector(); status(!!data.ready, proposalId ? 'Candidate — Apply or Reject' : 'Compiled snapshot');
            if (!proposalId && !draftDirty) $('diagnostics').hidden = true;
        } else if (data.type === 'status') {
            if (data.clearProposal) { proposalId = undefined; $('candidate').hidden = true; }
            status(!!data.ready,data.message);
        } else if (data.type === 'error' || data.type === 'notice') notice(data.message);
    });
    frame.addEventListener('load', view);
    $('design').onclick = () => { mode = 'design'; view(); }; $('play').onclick = () => { mode = 'play'; view(); };
    $('zoom').onchange = zoom; $('refresh').onclick = () => send('refresh'); $('source').onclick = () => send('reveal');
    $('undo').onclick = () => send('undo'); $('redo').onclick = () => send('redo');
    $('copy').onclick = () => send('copyRequest', { prompt:$('prompt').value }); $('issue').onclick = () => edit('issue',$('prompt').value);
    $('proposal').oninput = () => { draftDirty = true; if (draftGeneration === undefined) draftGeneration = generation; };
    const reset = button('Reset draft from source', () => { if (!draftDirty || confirm('Discard this source draft?')) { $('proposal').value = slide()?.source || ''; draftDirty = false; draftGeneration = generation; status(ready,$('status').textContent); } }, $('proposal').parentElement);
    reset.id = 'resetDraft';
    $('propose').onclick = () => send('propose',{value:$('proposal').value});
    $('diff').onclick = () => send('diff',{proposalId});
    $('apply').onclick = () => { draftDirty = false; send('applyProposal',{proposalId}); };
    $('reject').onclick = () => { draftDirty = false; send('reject'); };
    new ResizeObserver(zoom).observe($('viewport'));
    document.addEventListener('keydown', e => {
        if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
        if (mode === 'design' && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
            e.preventDefault(); const next = slideIndex + (e.key === 'ArrowRight' ? 1 : -1);
            if (manifest?.slides[next]) $('slides').children[next].click();
        }
    });
    status(false,'Building snapshot…'); send('ready');
})();
