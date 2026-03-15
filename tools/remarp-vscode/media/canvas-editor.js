/**
 * Remarp Canvas Visual Editor
 * SVG overlay for editing canvas DSL elements (icons, boxes, arrows).
 */
class CanvasVisualEditor {
    constructor(canvasContainer) {
        this.container = canvasContainer;
        this.elements = [];
        this.selectedElement = null;
        this.svgOverlay = null;
        this.timelineBar = null;
        this.currentStep = 0;
        this.maxStep = 0;
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.dragElement = null;
        this.waypointDragging = null;

        this._init();
    }

    _init() {
        this._createSvgOverlay();
        this._createTimelineBar();

        // Global mouse events
        document.addEventListener('mousemove', (e) => this._onMouseMove(e));
        document.addEventListener('mouseup', (e) => this._onMouseUp(e));
    }

    /**
     * Parse canvas DSL from slide content to extract element positions.
     * @param {string} slideContent - The raw slide content containing canvas DSL
     * @returns {Array} Array of parsed elements
     */
    parseCanvasDsl(slideContent) {
        const elements = [];
        const lines = slideContent.split('\n');
        let currentElement = null;

        for (const line of lines) {
            const trimmed = line.trim();

            // icon ID "Label" at X,Y size S
            const iconMatch = trimmed.match(/^icon\s+(\w+)\s+"([^"]+)"\s+at\s+(\d+),(\d+)(?:\s+size\s+(\d+))?/);
            if (iconMatch) {
                elements.push({
                    type: 'icon',
                    id: iconMatch[1],
                    label: iconMatch[2],
                    x: parseInt(iconMatch[3]),
                    y: parseInt(iconMatch[4]),
                    size: iconMatch[5] ? parseInt(iconMatch[5]) : 64,
                    width: iconMatch[5] ? parseInt(iconMatch[5]) : 64,
                    height: iconMatch[5] ? parseInt(iconMatch[5]) : 64,
                    step: 0,
                    animatePath: null
                });
                currentElement = elements[elements.length - 1];
                continue;
            }

            // box ID "Label" at X,Y size W,H color C
            const boxMatch = trimmed.match(/^box\s+(\w+)\s+"([^"]+)"\s+at\s+(\d+),(\d+)\s+size\s+(\d+),(\d+)(?:\s+color\s+(\S+))?/);
            if (boxMatch) {
                elements.push({
                    type: 'box',
                    id: boxMatch[1],
                    label: boxMatch[2],
                    x: parseInt(boxMatch[3]),
                    y: parseInt(boxMatch[4]),
                    width: parseInt(boxMatch[5]),
                    height: parseInt(boxMatch[6]),
                    color: boxMatch[7] || '#3498db',
                    step: 0,
                    animatePath: null
                });
                currentElement = elements[elements.length - 1];
                continue;
            }

            // circle "Label" at X,Y radius R
            const circleMatch = trimmed.match(/^circle\s+"([^"]+)"\s+at\s+(\d+),(\d+)\s+radius\s+(\d+)/);
            if (circleMatch) {
                const r = parseInt(circleMatch[4]);
                elements.push({
                    type: 'circle',
                    id: `circle_${elements.length}`,
                    label: circleMatch[1],
                    x: parseInt(circleMatch[2]),
                    y: parseInt(circleMatch[3]),
                    radius: r,
                    width: r * 2,
                    height: r * 2,
                    step: 0,
                    animatePath: null
                });
                currentElement = elements[elements.length - 1];
                continue;
            }

            // arrow A -> B "label" step N
            const arrowMatch = trimmed.match(/^arrow\s+(\w+)\s*->\s*(\w+)(?:\s+"([^"]+)")?(?:\s+step\s+(\d+))?/);
            if (arrowMatch) {
                const step = arrowMatch[4] ? parseInt(arrowMatch[4]) : 0;
                elements.push({
                    type: 'arrow',
                    id: `arrow_${arrowMatch[1]}_${arrowMatch[2]}`,
                    from: arrowMatch[1],
                    to: arrowMatch[2],
                    label: arrowMatch[3] || '',
                    step: step,
                    x: 0,
                    y: 0,
                    width: 0,
                    height: 0
                });
                this.maxStep = Math.max(this.maxStep, step);
                continue;
            }

            // text "..." at X,Y
            const textMatch = trimmed.match(/^text\s+"([^"]+)"\s+at\s+(\d+),(\d+)/);
            if (textMatch) {
                elements.push({
                    type: 'text',
                    id: `text_${elements.length}`,
                    label: textMatch[1],
                    x: parseInt(textMatch[2]),
                    y: parseInt(textMatch[3]),
                    width: 100,
                    height: 24,
                    step: 0,
                    animatePath: null
                });
                currentElement = elements[elements.length - 1];
                continue;
            }

            // step N for previous element
            const stepMatch = trimmed.match(/^step\s+(\d+)/);
            if (stepMatch && currentElement) {
                currentElement.step = parseInt(stepMatch[1]);
                this.maxStep = Math.max(this.maxStep, currentElement.step);
                continue;
            }

            // animate-path: (x,y) -> (x,y) -> ... duration Xs easing
            const animateMatch = trimmed.match(/^animate-path:\s*(.+)/);
            if (animateMatch && currentElement) {
                const pathStr = animateMatch[1];
                const waypoints = [];
                const pointMatches = pathStr.matchAll(/\((\d+),(\d+)\)/g);
                for (const m of pointMatches) {
                    waypoints.push({ x: parseInt(m[1]), y: parseInt(m[2]) });
                }
                const durationMatch = pathStr.match(/duration\s+([\d.]+)s/);
                const easingMatch = pathStr.match(/easing\s+(\w+)/);
                currentElement.animatePath = {
                    waypoints: waypoints,
                    duration: durationMatch ? parseFloat(durationMatch[1]) : 1,
                    easing: easingMatch ? easingMatch[1] : 'ease'
                };
                continue;
            }

            // group "Name" containing A,B
            const groupMatch = trimmed.match(/^group\s+"([^"]+)"\s+containing\s+(.+)/);
            if (groupMatch) {
                const members = groupMatch[2].split(',').map(s => s.trim());
                elements.push({
                    type: 'group',
                    id: `group_${elements.length}`,
                    label: groupMatch[1],
                    members: members,
                    x: 0,
                    y: 0,
                    width: 0,
                    height: 0,
                    step: 0
                });
                continue;
            }
        }

        this.elements = elements;
        return elements;
    }

    /**
     * Create transparent SVG layer over the canvas.
     */
    _createSvgOverlay() {
        const rect = this.container.getBoundingClientRect();

        this.svgOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svgOverlay.classList.add('remarp-canvas-overlay');
        this.svgOverlay.setAttribute('width', rect.width);
        this.svgOverlay.setAttribute('height', rect.height);
        this.svgOverlay.style.position = 'absolute';
        this.svgOverlay.style.top = '0';
        this.svgOverlay.style.left = '0';

        // Make container positioned if not already
        const containerStyle = window.getComputedStyle(this.container.parentElement);
        if (containerStyle.position === 'static') {
            this.container.parentElement.style.position = 'relative';
        }

        this.container.parentElement.appendChild(this.svgOverlay);
    }

    /**
     * Render hitbox rectangles/circles on the SVG for each element.
     * @param {Array} elements - Parsed canvas elements
     */
    renderSvgOverlay(elements) {
        // Clear existing
        this.svgOverlay.innerHTML = '';

        // Filter by current step
        const visibleElements = elements.filter(el => el.step <= this.currentStep);

        for (const el of visibleElements) {
            if (el.type === 'arrow' || el.type === 'group') continue;

            let hitbox;

            if (el.type === 'circle') {
                hitbox = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                hitbox.setAttribute('cx', el.x);
                hitbox.setAttribute('cy', el.y);
                hitbox.setAttribute('r', el.radius);
            } else {
                hitbox = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                hitbox.setAttribute('x', el.x);
                hitbox.setAttribute('y', el.y);
                hitbox.setAttribute('width', el.width);
                hitbox.setAttribute('height', el.height);
            }

            hitbox.classList.add('remarp-canvas-hitbox');
            hitbox.dataset.elementId = el.id;

            // Click to select
            hitbox.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectCanvasElement(el.id);
            });

            // Mousedown for drag
            hitbox.addEventListener('mousedown', (e) => {
                if (e.button !== 0) return;
                this.isDragging = true;
                this.dragElement = el;
                this.dragStart = { x: e.clientX, y: e.clientY };
                e.preventDefault();
            });

            this.svgOverlay.appendChild(hitbox);
        }

        // Render waypoints for selected element with animate-path
        if (this.selectedElement && this.selectedElement.animatePath) {
            this.renderWaypoints(this.selectedElement);
        }
    }

    /**
     * Select a canvas element by ID.
     * @param {string} elementId - The element ID
     */
    selectCanvasElement(elementId) {
        // Deselect previous
        this.svgOverlay.querySelectorAll('.selected').forEach(el => {
            el.classList.remove('selected');
        });

        const element = this.elements.find(el => el.id === elementId);
        if (!element) return;

        this.selectedElement = element;

        // Highlight hitbox
        const hitbox = this.svgOverlay.querySelector(`[data-element-id="${elementId}"]`);
        if (hitbox) {
            hitbox.classList.add('selected');
        }

        // Show waypoints if has animate-path
        if (element.animatePath) {
            this.renderWaypoints(element);
        }

        // Notify extension
        window._remarpPostMessage({
            command: 'canvasElementSelected',
            elementId: elementId,
            element: element
        });
    }

    /**
     * Render animate-path waypoints for an element.
     * @param {Object} element - The element with animatePath
     */
    renderWaypoints(element) {
        if (!element.animatePath || !element.animatePath.waypoints.length) return;

        const waypoints = element.animatePath.waypoints;

        // Draw connecting lines
        if (waypoints.length > 1) {
            const points = waypoints.map(w => `${w.x},${w.y}`).join(' ');
            const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
            polyline.setAttribute('points', points);
            polyline.classList.add('remarp-waypoint-path');
            this.svgOverlay.appendChild(polyline);

            // Clickable line segments to add waypoints
            for (let i = 0; i < waypoints.length - 1; i++) {
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', waypoints[i].x);
                line.setAttribute('y1', waypoints[i].y);
                line.setAttribute('x2', waypoints[i + 1].x);
                line.setAttribute('y2', waypoints[i + 1].y);
                line.classList.add('remarp-waypoint-line');
                line.dataset.segmentIndex = i;

                line.addEventListener('click', (e) => {
                    const rect = this.svgOverlay.getBoundingClientRect();
                    const x = Math.round(e.clientX - rect.left);
                    const y = Math.round(e.clientY - rect.top);
                    this._addWaypoint(element, parseInt(line.dataset.segmentIndex) + 1, x, y);
                });

                this.svgOverlay.appendChild(line);
            }
        }

        // Draw waypoint circles
        waypoints.forEach((wp, index) => {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', wp.x);
            circle.setAttribute('cy', wp.y);
            circle.setAttribute('r', 6);
            circle.classList.add('remarp-waypoint');
            circle.dataset.waypointIndex = index;
            circle.dataset.elementId = element.id;

            // Drag waypoint
            circle.addEventListener('mousedown', (e) => {
                if (e.button !== 0) return;
                this.waypointDragging = { elementId: element.id, index: index };
                this.dragStart = { x: e.clientX, y: e.clientY };
                e.preventDefault();
                e.stopPropagation();
            });

            // Double-click to delete waypoint
            circle.addEventListener('dblclick', (e) => {
                e.stopPropagation();
                this._deleteWaypoint(element, index);
            });

            this.svgOverlay.appendChild(circle);
        });
    }

    /**
     * Add a new waypoint at the given position.
     */
    _addWaypoint(element, insertIndex, x, y) {
        if (!element.animatePath) return;

        element.animatePath.waypoints.splice(insertIndex, 0, { x, y });
        this.renderSvgOverlay(this.elements);

        window._remarpPostMessage({
            command: 'waypointChanged',
            elementId: element.id,
            action: 'add',
            index: insertIndex,
            waypoints: element.animatePath.waypoints
        });
    }

    /**
     * Delete a waypoint at the given index.
     */
    _deleteWaypoint(element, index) {
        if (!element.animatePath || element.animatePath.waypoints.length <= 2) return;

        element.animatePath.waypoints.splice(index, 1);
        this.renderSvgOverlay(this.elements);

        window._remarpPostMessage({
            command: 'waypointChanged',
            elementId: element.id,
            action: 'delete',
            index: index,
            waypoints: element.animatePath.waypoints
        });
    }

    _onMouseMove(e) {
        if (this.waypointDragging) {
            const rect = this.svgOverlay.getBoundingClientRect();
            const x = Math.round(e.clientX - rect.left);
            const y = Math.round(e.clientY - rect.top);

            const element = this.elements.find(el => el.id === this.waypointDragging.elementId);
            if (element && element.animatePath) {
                element.animatePath.waypoints[this.waypointDragging.index] = { x, y };
                this.renderSvgOverlay(this.elements);
            }
        } else if (this.isDragging && this.dragElement) {
            const dx = e.clientX - this.dragStart.x;
            const dy = e.clientY - this.dragStart.y;

            // Update element position
            const hitbox = this.svgOverlay.querySelector(`[data-element-id="${this.dragElement.id}"]`);
            if (hitbox) {
                if (this.dragElement.type === 'circle') {
                    hitbox.setAttribute('cx', this.dragElement.x + dx);
                    hitbox.setAttribute('cy', this.dragElement.y + dy);
                } else {
                    hitbox.setAttribute('x', this.dragElement.x + dx);
                    hitbox.setAttribute('y', this.dragElement.y + dy);
                }
            }
        }
    }

    _onMouseUp(e) {
        if (this.waypointDragging) {
            const element = this.elements.find(el => el.id === this.waypointDragging.elementId);
            if (element && element.animatePath) {
                window._remarpPostMessage({
                    command: 'waypointChanged',
                    elementId: element.id,
                    action: 'move',
                    index: this.waypointDragging.index,
                    waypoints: element.animatePath.waypoints
                });
            }
            this.waypointDragging = null;
        }

        if (this.isDragging && this.dragElement) {
            const dx = e.clientX - this.dragStart.x;
            const dy = e.clientY - this.dragStart.y;

            if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
                // Update element's stored position
                this.dragElement.x += dx;
                this.dragElement.y += dy;

                window._remarpPostMessage({
                    command: 'canvasElementMoved',
                    elementId: this.dragElement.id,
                    position: { x: this.dragElement.x, y: this.dragElement.y }
                });
            }

            this.isDragging = false;
            this.dragElement = null;
        }
    }

    /**
     * Create step timeline bar below the canvas.
     */
    _createTimelineBar() {
        const timeline = document.createElement('div');
        timeline.className = 'remarp-timeline';

        const label = document.createElement('span');
        label.className = 'remarp-timeline-label';
        label.textContent = 'Steps:';
        timeline.appendChild(label);

        // Will be populated when elements are parsed
        this.timelineBar = timeline;
        document.body.appendChild(timeline);
    }

    /**
     * Update timeline buttons based on maxStep.
     */
    updateTimeline() {
        if (!this.timelineBar) return;

        // Remove existing step buttons
        this.timelineBar.querySelectorAll('.remarp-step-btn').forEach(btn => btn.remove());

        // Create step buttons
        for (let i = 0; i <= this.maxStep; i++) {
            const btn = document.createElement('button');
            btn.className = 'remarp-step-btn';
            if (i === this.currentStep) btn.classList.add('active');
            btn.textContent = i.toString();
            btn.addEventListener('click', () => this.goToStep(i));
            this.timelineBar.appendChild(btn);
        }

        // Add "+" button for new step
        const addBtn = document.createElement('button');
        addBtn.className = 'remarp-step-btn add-step';
        addBtn.textContent = '+';
        addBtn.addEventListener('click', () => {
            this.maxStep++;
            this.updateTimeline();
            window._remarpPostMessage({
                command: 'canvasStepAdded',
                newMaxStep: this.maxStep
            });
        });
        this.timelineBar.appendChild(addBtn);
    }

    /**
     * Navigate to a specific step.
     * @param {number} step - The step number
     */
    goToStep(step) {
        this.currentStep = step;
        this.renderSvgOverlay(this.elements);
        this.updateTimeline();

        window._remarpPostMessage({
            command: 'canvasStepChanged',
            step: step
        });
    }

    /**
     * Load canvas content and initialize the editor.
     * @param {string} slideContent - The slide content
     */
    loadContent(slideContent) {
        this.parseCanvasDsl(slideContent);
        this.updateTimeline();
        this.renderSvgOverlay(this.elements);
    }
}

// Expose class for lazy initialization (same pattern as edit-mode.js)
window._RemarpCanvasEditorClass = class RemarpCanvasEditorManager {
    constructor() {
        this._editors = [];
        this._init();
    }

    _init() {
        this._initCanvasEditors();
        // Re-initialize when slide content changes
        const observer = new MutationObserver(() => this._initCanvasEditors());
        observer.observe(document.body, { childList: true, subtree: true });
    }

    _initCanvasEditors() {
        document.querySelectorAll('.canvas-placeholder, canvas, [data-canvas]').forEach(canvas => {
            if (canvas._remarpCanvasEditor) return; // Already initialized

            const editor = new CanvasVisualEditor(canvas);
            canvas._remarpCanvasEditor = editor;
            this._editors.push(editor);

            // If there's slide content available, load it
            const slideEl = canvas.closest('[data-remarp-id]');
            if (slideEl && slideEl.dataset.canvasContent) {
                editor.loadContent(slideEl.dataset.canvasContent);
            }
        });
    }
};

// Initialize immediately if edit mode is already active
if (window._remarpEditMode) {
    window._remarpCanvasEditor = new window._RemarpCanvasEditorClass();
}
