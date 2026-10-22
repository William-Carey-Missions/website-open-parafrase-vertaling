/* Dezelfde boekkeuze in het overzicht en de lezer. */
(function () {
    const key = 'sv2026_vertaalopties';
    function state() {
        try { return JSON.parse(localStorage.getItem(key) || '{}'); } catch (_) { return {}; }
    }
    function apply() {
        const enabled = state().ethiopischeBoeken === 'aan';
        document.querySelectorAll('[data-ethiopic-books]').forEach(group => { group.hidden = !enabled; });
        const toggle = document.getElementById('show-ethiopic-books');
        if (toggle) toggle.checked = enabled;
    }
    document.addEventListener('DOMContentLoaded', () => {
        apply();
        document.getElementById('show-ethiopic-books')?.addEventListener('change', event => {
            const value = event.target.checked ? 'aan' : 'uit';
            const saved = state();
            saved.ethiopischeBoeken = value;
            localStorage.setItem(key, JSON.stringify(saved));
            if (window.Opties) window.Opties.state.ethiopischeBoeken = value;
            apply();
        });
    });
    window.addEventListener('storage', apply);
})();
