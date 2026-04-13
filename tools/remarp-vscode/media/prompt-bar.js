// Prompt bar: issue annotation input + issue badge removal
(function () {
    const api = window._vscodeApi;
    if (!api) { return; }

    const slideIndex = parseInt(document.body.dataset.slideIndex || '0', 10);
    const input = document.getElementById('promptInput');
    const form = document.getElementById('promptForm');

    // ─── State persistence across re-renders ───
    const saved = api.getState() || {};
    if (input && saved.promptText) {
        input.value = saved.promptText;
    }

    // Save text on every keystroke
    if (input) {
        input.addEventListener('input', () => {
            const s = api.getState() || {};
            api.setState({ ...s, promptText: input.value });
        });

        // Track focus
        input.addEventListener('focus', () => {
            const s = api.getState() || {};
            api.setState({ ...s, promptFocused: true, promptCursor: input.selectionStart });
        });
        input.addEventListener('blur', () => {
            const s = api.getState() || {};
            api.setState({ ...s, promptFocused: false });
        });
    }

    // Restore focus if it was active before re-render
    if (input && saved.promptFocused) {
        input.focus();
        if (saved.promptCursor != null) {
            input.setSelectionRange(saved.promptCursor, saved.promptCursor);
        }
    }

    // ─── Submit: add issue annotation ───
    function handleSubmit() {
        if (!input) { return; }
        const text = input.value.trim();
        if (!text) { return; }
        window._remarpPostMessage({ command: 'addIssue', text: text, slideIndex: slideIndex });
        input.value = '';
        api.setState({ ...api.getState(), promptText: '' });
    }

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            handleSubmit();
        });
    }

    // Direct click handler for the submit button (fallback for webview)
    var promptSubmitBtn = document.querySelector('.prompt-submit');
    if (promptSubmitBtn) {
        promptSubmitBtn.addEventListener('click', (e) => {
            e.preventDefault();
            handleSubmit();
        });
    }

    // ─── Issue badge removal ───
    document.querySelectorAll('.issue-remove').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const issueText = btn.getAttribute('data-issue');
            if (issueText) {
                window._remarpPostMessage({ command: 'removeIssue', issueText: issueText, slideIndex: slideIndex });
            }
        });
    });

    // ─── Submit all issues to Claude ───
    const submitBtn = document.getElementById('submitAllBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', () => {
            window._remarpPostMessage({ command: 'submitAllIssues' });
        });
    }
})();
