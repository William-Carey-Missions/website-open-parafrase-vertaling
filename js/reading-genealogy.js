/* De stamboom blijft rechtstreeks verbonden met de bron bij Open Gods Word. */
(function () {
    const root = document.getElementById('verses-container');
    if (!root) return;

    function stamboomAdres() {
        const arabisch = window.Opties?.state?.arabischeNamen === 'aan';
        return 'https://opengodsword.com/stamboom-embed.html' + (arabisch ? '?namen=arabisch' : '');
    }

    function enhance() {
        root.querySelectorAll('.opw-leesindeling').forEach(layout => {
            const row = layout.querySelector('.verse-row');
            if (row?.dataset.book !== 'genesis' || Number(row.dataset.chapter) !== 5) return;
            let panel = layout.querySelector('.opw-genealogy');
            if (!panel) {
                panel = document.createElement('section');
                panel.className = 'opw-genealogy';
                panel.setAttribute('aria-label', 'Stamboom bij Genesis 5');
                const heading = document.createElement('h2');
                heading.textContent = 'Van Adam tot Noach';
                const frame = document.createElement('iframe');
                frame.src = stamboomAdres();
                frame.title = 'Interactieve stamboom bij Genesis 5';
                frame.loading = 'lazy';
                const link = document.createElement('a');
                link.href = 'https://opengodsword.com/stamboom.html';
                link.target = '_blank';
                link.rel = 'noopener';
                link.textContent = 'Bekijk de hele stamboom bij Open Gods Word →';
                panel.append(heading, frame, link);
            }
            const kop = panel.querySelector('h2');
            if (kop) kop.textContent = window.Opties?.transformOPV ? Opties.transformOPV('Van Adam tot Noach') : 'Van Adam tot Noach';
            const frame = panel.querySelector('iframe');
            if (frame && frame.getAttribute('src') !== stamboomAdres()) frame.setAttribute('src', stamboomAdres());
            const mobile = window.matchMedia('(max-width: 1100px), (hover: none), (pointer: coarse)').matches;
            const destination = mobile ? layout.querySelector('.opw-leeskolom') : layout.querySelector('.opw-sidecar');
            if (!destination) return;
            if (mobile) {
                const heading = destination.querySelector('.opv-hoofdstukkop');
                if (heading && panel.previousElementSibling !== heading) heading.after(panel);
            } else if (panel.parentElement !== destination) destination.prepend(panel);
        });
    }
    document.addEventListener('DOMContentLoaded', enhance);
    document.addEventListener('opv:hoofdstuk-getoond', enhance);
    window.addEventListener('resize', enhance);
    window.addEventListener('ov:opties-gewijzigd', enhance);
})();
