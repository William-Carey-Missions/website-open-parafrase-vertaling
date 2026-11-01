// De lezer en scripts/build_leespaginas.py moeten namen hetzelfde behandelen.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync, existsSync } = require('node:fs');
const { resolve } = require('node:path');
const vm = require('node:vm');
const lees = pad => readFileSync(resolve(__dirname, '..', pad), 'utf8');

function uitleg(gegevens) {
    const context = vm.createContext({ window: { NAAMSBETEKENISSEN: gegevens } });
    vm.runInContext(lees('js/naamuitleg.js'), context);
    return context.window.NaamUitleg;
}

test('namen krijgen hun betekenis, gewone woorden niet', () => {
    const { voegToe } = uitleg({ namen: { Dan: 'rechter', Mozes: 'uit het water getrokken', Abrahams: 'vader van velen' }, alleenMiddenInZin: ['Dan'] });
    assert.equal(voegToe('Dan ging Mozes weg. Dan zag Dan het.'), 'Dan ging Mozes (uit het water getrokken) weg. Dan zag Dan (rechter) het.');
    assert.equal(voegToe('<span class="Mozes">Mozes</span> en Abrahams zoon'), '<span class="Mozes">Mozes (uit het water getrokken)</span> en Abrahams (vader van velen) zoon');
    assert.equal(voegToe('Mozesje en Dan'), 'Mozesje en Dan (rechter)');
    assert.equal(voegToe('Hij zei: Dan komt het goed'), 'Hij zei: Dan komt het goed');
    assert.equal(voegToe('Mozes-Dan en Dan-Mozes'), 'Mozes-Dan en Dan-Mozes');
});

test('namen met accenten en een lege invoer', () => {
    const { voegToe } = uitleg({ namen: { 'Gabriël': 'held van God' }, alleenMiddenInZin: [] });
    assert.equal(voegToe('De engel Gabriël kwam.'), 'De engel Gabriël (held van God) kwam.');
    assert.equal(voegToe('Gabriëlle kwam.'), 'Gabriëlle kwam.');
    assert.equal(voegToe(''), '');
});

test('geen lookbehind: die breekt de lezer op iPadOS 15', () => {
    assert.doesNotMatch(lees('js/naamuitleg.js'), /\(\?<[=!]/);
});

test('de gegevens voldoen aan de vorm', { skip: !existsSync(resolve(__dirname, '..', 'js/naamsbetekenissen.js')) }, () => {
    const context = vm.createContext({ window: {} });
    vm.runInContext(lees('js/naamsbetekenissen.js'), context);
    const { namen, alleenMiddenInZin } = context.window.NAAMSBETEKENISSEN;
    assert.ok(Object.keys(namen).length > 300);
    for (const [naam, betekenis] of Object.entries(namen)) {
        assert.doesNotMatch(betekenis, /[.?!()"]/, naam);
        assert.ok(betekenis.split(' ').length <= 7, naam);
    }
    for (const naam of alleenMiddenInZin) assert.ok(namen[naam], naam);
    assert.ok(alleenMiddenInZin.includes('Dan') || !namen.Dan);
    assert.ok(alleenMiddenInZin.includes('Er') || !namen.Er);
});

test('een naam krijgt zijn betekenis maar één keer per hoofdstuk', () => {
    const { voegToe } = uitleg({ namen: { Abraham: 'vader van velen', Abrahams: 'vader van velen', Izak: 'hij lacht' }, alleenMiddenInZin: [] });
    const gezien = new Set();
    assert.equal(voegToe('Abraham en Izak gingen.', undefined, gezien), 'Abraham (vader van velen) en Izak (hij lacht) gingen.');
    assert.equal(voegToe('Toen zag Abraham het, en Izak ook.', undefined, gezien), 'Toen zag Abraham het, en Izak ook.');
    assert.equal(voegToe('Dat is Abrahams zoon.', undefined, gezien), 'Dat is Abrahams zoon.');
    assert.equal(voegToe('Abraham ging.', undefined, new Set()), 'Abraham (vader van velen) ging.', 'een nieuw hoofdstuk begint opnieuw');
    assert.equal(voegToe('Abraham en Abraham.', undefined, new Set()), 'Abraham (vader van velen) en Abraham.', 'ook binnen een vers');
});

test('een overgeslagen woord telt niet als genoemde naam', () => {
    const { voegToe } = uitleg({ namen: { Dan: 'rechter' }, alleenMiddenInZin: ['Dan'] });
    const gezien = new Set();
    assert.equal(voegToe('Dan ging hij naar Dan.', undefined, gezien), 'Dan ging hij naar Dan (rechter).');
    assert.equal(voegToe('En Dan kwam.', undefined, gezien), 'En Dan kwam.');
});

test('de lezer houdt per hoofdstuk bij welke namen al zijn uitgelegd', () => {
    assert.match(lees('js/chapter-renderer.js'), /NaamUitleg\.voegToe\(openVertaling, undefined, uitgelegdeNamen\)/);
});
