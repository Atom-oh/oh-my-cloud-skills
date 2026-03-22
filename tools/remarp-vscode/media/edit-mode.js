/**
 * Remarp Visual Editor - Edit Mode Client
 * Handles element selection, drag, resize, and property editing in the webview.
 */
class RemarpVisualEditor {
    constructor() {
        this.selectedElement = null;
        this.isDragging = false;
        this.isResizing = false;
        this.dragStart = { x: 0, y: 0 };
        this.originalTransform = { x: 0, y: 0 };
        this.resizeHandle = null;
        this.originalRect = null;
        this.propertyPanel = null;
        this.handles = [];
        this.elementIdBadge = null;

        this._init();
    }

    _init() {
        // Create edit mode indicator
        this._createEditIndicator();

        // Create property panel
        this._createPropertyPanel();

        // Intercept clicks on data-remarp-id elements
        document.addEventListener('click', (e) => {
            const target = e.target.closest('[data-remarp-id]');
            if (target && !e.target.closest('.remarp-handle') && !e.target.closest('.remarp-property-panel')) {
                e.preventDefault();
                e.stopPropagation();
                this.selectElement(target);
            } else if (!e.target.closest('.remarp-property-panel') && !e.target.closest('.remarp-handle') && !e.target.closest('[data-remarp-id]')) {
                this.deselectAll();
            }
        });

        // Keyboard: Escape to deselect
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.deselectAll();
            }
            // Block navigation keys in edit mode to prevent slide changes
            if (['ArrowLeft', 'ArrowRight', ' ', 'PageUp', 'PageDown', 'Home'].includes(e.key)) {
                e.preventDefault();
                e.stopPropagation();
            }
        }, true); // capture phase to block before preview.js handlers

        // Global mouse events for drag/resize
        document.addEventListener('mousemove', (e) => this._onMouseMove(e));
        document.addEventListener('mouseup', (e) => this._onMouseUp(e));
    }

    _createEditIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'remarp-edit-indicator';
        indicator.textContent = 'Edit Mode';
        document.body.appendChild(indicator);
    }

    selectElement(el) {
        this.deselectAll();
        this.selectedElement = el;
        el.classList.add('remarp-selected');
        this._showHandles(el);
        this._showElementId(el);
        this._updatePropertyPanel(el);
        this._setupDrag(el);

        // Notify extension
        window._remarpPostMessage({
            command: 'elementSelected',
            elementId: el.dataset.remarpId,
            rect: this._getElementRect(el)
        });
    }

    deselectAll() {
        if (this.selectedElement) {
            this.selectedElement.classList.remove('remarp-selected');
        }
        this.selectedElement = null;
        this._removeHandles();
        this._removeElementId();
        this._hidePropertyPanel();
    }

    _getElementRect(el) {
        const rect = el.getBoundingClientRect();
        return {
            x: rect.left,
            y: rect.top,
            width: rect.width,
            height: rect.height
        };
    }

    _showHandles(el) {
        const directions = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
        directions.forEach(dir => {
            const handle = document.createElement('div');
            handle.className = `remarp-handle remarp-handle-${dir}`;
            handle.dataset.direction = dir;
            el.appendChild(handle);
            this.handles.push(handle);
            this._setupResize(handle, el, dir);
        });
    }

    _removeHandles() {
        this.handles.forEach(handle => handle.remove());
        this.handles = [];
    }

    _showElementId(el) {
        this._removeElementId();
        const badge = document.createElement('div');
        badge.className = 'remarp-element-id';
        badge.textContent = el.dataset.remarpId;
        el.appendChild(badge);
        this.elementIdBadge = badge;
    }

    _removeElementId() {
        if (this.elementIdBadge) {
            this.elementIdBadge.remove();
            this.elementIdBadge = null;
        }
    }

    _setupDrag(el) {
        el.addEventListener('mousedown', (e) => {
            if (e.target.closest('.remarp-handle')) return;
            if (e.button !== 0) return;

            // If click target is inside a nested [data-remarp-id], select the inner element instead of dragging
            const innerTarget = e.target.closest('[data-remarp-id]');
            if (innerTarget && innerTarget !== el) {
                e.preventDefault();
                e.stopPropagation();
                this.selectElement(innerTarget);
                return;
            }

            this.isDragging = true;
            this.dragStart = { x: e.clientX, y: e.clientY };

            // Parse current transform
            const transform = el.style.transform || '';
            const match = transform.match(/translate\((-?\d+(?:\.\d+)?)px,\s*(-?\d+(?:\.\d+)?)px\)/);
            this.originalTransform = match
                ? { x: parseFloat(match[1]), y: parseFloat(match[2]) }
                : { x: 0, y: 0 };

            e.preventDefault();
        });
    }

    _setupResize(handle, el, direction) {
        handle.addEventListener('mousedown', (e) => {
            if (e.button !== 0) return;

            this.isResizing = true;
            this.resizeHandle = direction;
            this.dragStart = { x: e.clientX, y: e.clientY };
            this.originalRect = this._getElementRect(el);

            e.preventDefault();
            e.stopPropagation();
        });
    }

    _onMouseMove(e) {
        if (!this.selectedElement) return;

        if (this.isDragging) {
            const dx = e.clientX - this.dragStart.x;
            const dy = e.clientY - this.dragStart.y;
            const newX = this.originalTransform.x + dx;
            const newY = this.originalTransform.y + dy;

            this.selectedElement.style.transform = `translate(${newX}px, ${newY}px)`;
        } else if (this.isResizing) {
            this._handleResize(e);
        }
    }

    _handleResize(e) {
        const el = this.selectedElement;
        const dx = e.clientX - this.dragStart.x;
        const dy = e.clientY - this.dragStart.y;
        const dir = this.resizeHandle;

        let newWidth = this.originalRect.width;
        let newHeight = this.originalRect.height;

        // Adjust dimensions based on handle direction
        if (dir.includes('e')) newWidth = this.originalRect.width + dx;
        if (dir.includes('w')) newWidth = this.originalRect.width - dx;
        if (dir.includes('s')) newHeight = this.originalRect.height + dy;
        if (dir.includes('n')) newHeight = this.originalRect.height - dy;

        // Apply minimum sizes
        newWidth = Math.max(50, newWidth);
        newHeight = Math.max(30, newHeight);

        el.style.width = `${newWidth}px`;
        el.style.height = `${newHeight}px`;
    }

    _onMouseUp(e) {
        if (this.isDragging && this.selectedElement) {
            const transform = this.selectedElement.style.transform || '';
            const match = transform.match(/translate\((-?\d+(?:\.\d+)?)px,\s*(-?\d+(?:\.\d+)?)px\)/);
            if (match) {
                window._remarpPostMessage({
                    command: 'elementMoved',
                    elementId: this.selectedElement.dataset.remarpId,
                    delta: { x: parseFloat(match[1]), y: parseFloat(match[2]) }
                });
            }
        }

        if (this.isResizing && this.selectedElement) {
            window._remarpPostMessage({
                command: 'elementResized',
                elementId: this.selectedElement.dataset.remarpId,
                size: {
                    width: this.selectedElement.offsetWidth,
                    height: this.selectedElement.offsetHeight
                }
            });
        }

        this.isDragging = false;
        this.isResizing = false;
        this.resizeHandle = null;
    }

    _createPropertyPanel() {
        const panel = document.createElement('div');
        panel.className = 'remarp-property-panel';
        panel.innerHTML = `
            <div class="remarp-property-panel-header">
                <span>Properties</span>
                <button class="remarp-property-panel-close">&times;</button>
            </div>
            <div class="remarp-property-panel-body">
                <div class="remarp-property-group">
                    <div class="remarp-property-group-title">Position</div>
                    <div class="remarp-property-row">
                        <label class="remarp-property-label">X</label>
                        <input type="text" class="remarp-property-input" data-prop="posX" placeholder="0">
                    </div>
                    <div class="remarp-property-row">
                        <label class="remarp-property-label">Y</label>
                        <input type="text" class="remarp-property-input" data-prop="posY" placeholder="0">
                    </div>
                </div>
                <div class="remarp-property-group">
                    <div class="remarp-property-group-title">Dimensions</div>
                    <div class="remarp-property-row">
                        <label class="remarp-property-label">Width</label>
                        <input type="text" class="remarp-property-input" data-prop="width">
                    </div>
                    <div class="remarp-property-row">
                        <label class="remarp-property-label">Height</label>
                        <input type="text" class="remarp-property-input" data-prop="height">
                    </div>
                </div>
                <div class="remarp-property-group">
                    <div class="remarp-property-group-title">Spacing</div>
                    <div class="remarp-property-row">
                        <label class="remarp-property-label">Padding</label>
                        <input type="text" class="remarp-property-input" data-prop="padding">
                    </div>
                    <div class="remarp-property-row">
                        <label class="remarp-property-label">Margin</label>
                        <input type="text" class="remarp-property-input" data-prop="margin">
                    </div>
                </div>
                <div class="remarp-property-group">
                    <div class="remarp-property-group-title">Typography</div>
                    <div class="remarp-property-row">
                        <label class="remarp-property-label">Font Size</label>
                        <button class="remarp-font-btn" data-action="decreaseFont">A-</button>
                        <input type="text" class="remarp-property-input remarp-font-input" data-prop="fontSize">
                        <button class="remarp-font-btn" data-action="increaseFont">A+</button>
                    </div>
                    <div class="remarp-property-row">
                        <label class="remarp-property-label">Color</label>
                        <input type="color" class="remarp-property-input" data-prop="color">
                    </div>
                </div>
                <div class="remarp-property-group">
                    <div class="remarp-property-group-title">Background</div>
                    <div class="remarp-property-row">
                        <label class="remarp-property-label">Background</label>
                        <input type="color" class="remarp-property-input" data-prop="backgroundColor">
                    </div>
                    <div class="remarp-property-row">
                        <label class="remarp-property-label">Opacity</label>
                        <input type="text" class="remarp-property-input" data-prop="opacity" placeholder="0-1">
                    </div>
                </div>
                <div class="remarp-property-group">
                    <div class="remarp-property-group-title">Border</div>
                    <div class="remarp-property-row">
                        <label class="remarp-property-label">Radius</label>
                        <input type="text" class="remarp-property-input" data-prop="borderRadius">
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(panel);
        this.propertyPanel = panel;

        // Close button
        panel.querySelector('.remarp-property-panel-close').addEventListener('click', () => {
            this.deselectAll();
        });

        // Input change handlers
        panel.querySelectorAll('.remarp-property-input').forEach(input => {
            input.addEventListener('change', (e) => this._onPropertyChange(e));
        });

        // Font size A+/A- buttons
        panel.querySelectorAll('.remarp-font-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (!this.selectedElement) return;
                const fontInput = panel.querySelector('[data-prop="fontSize"]');
                const current = parseFloat(window.getComputedStyle(this.selectedElement).fontSize) || 16;
                const delta = btn.dataset.action === 'increaseFont' ? 2 : -2;
                const newSize = Math.max(8, current + delta) + 'px';
                this.selectedElement.style.fontSize = newSize;
                if (fontInput) fontInput.value = newSize;
                window._remarpPostMessage({
                    command: 'propertyChanged',
                    elementId: this.selectedElement.dataset.remarpId,
                    property: 'fontSize',
                    value: newSize
                });
            });
        });
    }

    _updatePropertyPanel(el) {
        if (!this.propertyPanel) return;

        const computed = window.getComputedStyle(el);
        const inputs = this.propertyPanel.querySelectorAll('.remarp-property-input');

        // Parse current transform for position X/Y
        const transform = el.style.transform || '';
        const tMatch = transform.match(/translate\((-?\d+(?:\.\d+)?)px,\s*(-?\d+(?:\.\d+)?)px\)/);
        const posX = tMatch ? parseFloat(tMatch[1]) : 0;
        const posY = tMatch ? parseFloat(tMatch[2]) : 0;

        inputs.forEach(input => {
            const prop = input.dataset.prop;

            if (prop === 'posX') {
                input.value = posX + 'px';
                return;
            }
            if (prop === 'posY') {
                input.value = posY + 'px';
                return;
            }

            let value = computed[prop] || '';

            // Convert rgb to hex for color inputs
            if (input.type === 'color' && value.startsWith('rgb')) {
                value = this._rgbToHex(value);
            }

            input.value = value;
        });

        this.propertyPanel.classList.add('visible');
    }

    _hidePropertyPanel() {
        if (this.propertyPanel) {
            this.propertyPanel.classList.remove('visible');
        }
    }

    _onPropertyChange(e) {
        if (!this.selectedElement) return;

        const input = e.target;
        const prop = input.dataset.prop;
        let value = input.value;

        // Handle position X/Y via transform
        if (prop === 'posX' || prop === 'posY') {
            const transform = this.selectedElement.style.transform || '';
            const tMatch = transform.match(/translate\((-?\d+(?:\.\d+)?)px,\s*(-?\d+(?:\.\d+)?)px\)/);
            let x = tMatch ? parseFloat(tMatch[1]) : 0;
            let y = tMatch ? parseFloat(tMatch[2]) : 0;
            const numVal = parseFloat(value) || 0;
            if (prop === 'posX') x = numVal;
            if (prop === 'posY') y = numVal;
            this.selectedElement.style.transform = `translate(${x}px, ${y}px)`;
            window._remarpPostMessage({
                command: 'elementMoved',
                elementId: this.selectedElement.dataset.remarpId,
                delta: { x, y }
            });
            return;
        }

        // Apply the style
        this.selectedElement.style[prop] = value;

        // Notify extension
        window._remarpPostMessage({
            command: 'propertyChanged',
            elementId: this.selectedElement.dataset.remarpId,
            property: prop,
            value: value
        });
    }

    _rgbToHex(rgb) {
        const match = rgb.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if (!match) return '#000000';

        const r = parseInt(match[1]).toString(16).padStart(2, '0');
        const g = parseInt(match[2]).toString(16).padStart(2, '0');
        const b = parseInt(match[3]).toString(16).padStart(2, '0');

        return `#${r}${g}${b}`;
    }
}

// Expose class for lazy initialization (MD preview activates on Edit button click)
window._RemarpVisualEditorClass = RemarpVisualEditor;

// Initialize immediately if edit mode is already active (HTML preview with edit mode enabled)
if (window._remarpEditMode) {
    window._remarpVisualEditor = new RemarpVisualEditor();
}
