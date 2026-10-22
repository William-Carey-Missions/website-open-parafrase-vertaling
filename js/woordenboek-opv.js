(function () {
    const input = document.getElementById('woordenboek-zoek');
    if (!input) return;
    const results = document.getElementById('woordenboek-resultaten');
    const detail = document.getElementById('woordenboek-lemma');
    const count = document.getElementById('woordenboek-telling');
    let terms = [];
    const currentBook = new URLSearchParams(location.search).get('boek') || '';
    const normalize = value => String(value || '').toLocaleLowerCase('nl').normalize('NFD').replace(/[\u0300-\u036f]/g, '');

    function element(tag, className, content) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (content != null) node.textContent = content;
        return node;
    }

    function show(term) {
        detail.replaceChildren();
        if (!term) {
            detail.append(element('h2', '', 'Kies een begrip'), element('p', '', 'Gebruik het zoekveld of volg een woordlink vanuit de Bijbeltekst.'));
            return;
        }
        detail.appendChild(element('p', 'opv-boven', term.categorie || 'Begrip'));
        detail.appendChild(element('h2', '', term.woord));
        const status = element('p', 'opw-lemma-status', 'Concept · menselijke beoordeling en onderbouwing vanuit de vroege kerk ontbreken nog.');
        detail.appendChild(status);
        const meanings = [...(term.betekenissen || [])].sort((a, b) =>
            Number(b.boek === currentBook) - Number(a.boek === currentBook));
        meanings.forEach((meaning, index) => {
            const section = element('section', 'opw-lemma-betekenis');
            section.appendChild(element('h3', '', meanings.length > 1 ? `Betekenis ${index + 1}` : 'Uitleg'));
            section.appendChild(element('p', '', meaning.uitleg));
            section.appendChild(element('p', 'opw-lemma-bron', `Bestaande begrippenlijst: ${meaning.boek}${meaning.ref ? ` · ${meaning.ref}` : ''}`));
            detail.appendChild(section);
        });
    }

    function select(word, changeHash = true) {
        const term = terms.find(item => normalize(item.woord) === normalize(word));
        show(term);
        if (term && changeHash) history.replaceState(null, '', `${location.pathname}${location.search}#${encodeURIComponent(term.woord.toLocaleLowerCase('nl'))}`);
    }

    function search() {
        const query = normalize(input.value.trim());
        const found = query ? terms.filter(item => normalize(item.woord).includes(query)) : terms;
        results.replaceChildren();
        found.slice(0, 60).forEach(term => {
            const item = element('li');
            const button = element('button', '', term.woord);
            button.type = 'button';
            button.addEventListener('click', () => select(term.woord));
            item.appendChild(button);
            results.appendChild(item);
        });
        count.textContent = `${found.length.toLocaleString('nl-NL')} begrippen${found.length > 60 ? ' · eerste 60 getoond' : ''}`;
    }

    fetch('/data/reading-dictionary.json')
        .then(response => { if (!response.ok) throw new Error('Woordenboek niet beschikbaar'); return response.json(); })
        .then(data => {
            terms = data.terms || [];
            const hash = decodeURIComponent(location.hash.slice(1));
            if (hash) {
                input.value = hash;
                select(hash, false);
            }
            search();
            input.addEventListener('input', search);
            window.addEventListener('hashchange', () => {
                const word = decodeURIComponent(location.hash.slice(1));
                input.value = word;
                select(word, false);
                search();
            });
        })
        .catch(() => { count.textContent = 'Woordenboek kon niet worden geladen.'; });
})();
