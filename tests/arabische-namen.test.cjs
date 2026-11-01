// De Arabische naamweergave voor moslimlezers, ook in de parafrase en de stamboom.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { existsSync, readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const vm = require('node:vm');
const root = resolve(__dirname, '..');
const lees = pad => readFileSync(resolve(root, pad), 'utf8');

async function opties() {
    const context = vm.createContext({
        window: {}, console,
        fetch: async url => ({ ok: true, json: async () => JSON.parse(lees(String(url))) }),
    });
    for (const file of ['js/optie-maten.js', 'js/opties.js']) {
        if (existsSync(resolve(root, file))) vm.runInContext(lees(file), context);
    }
    const current = context.window.Opties || vm.runInContext('Opties', context);
    current.state = { ...current.DEFAULTS };
    await current.loadArabischeNamen();
    return current;
}

test('de parafrase blijft standaard bij de Nederlandse namen', async () => {
    const current = await opties();
    assert.equal(current.state.arabischeNamen, 'uit');
    assert.equal(current.transformOPV('Noach en Jezus'), 'Noach en Jezus');
});

test('de optie zet namen in de parafrase om, ook Jezus maar niet Jezus Sirach', async () => {
    const current = await opties();
    current.state.arabischeNamen = 'aan';
    assert.equal(current.transformOPV('Abraham, Mozes en Noach'), 'Ibrahim, Musa en Nuh');
    assert.equal(current.transformOPV('Jezus zei tegen Jezus Sirach'), 'Isa zei tegen Jezus Sirach');
});

test('de godsnaamkeuze blijft naast de Arabische namen werken', async () => {
    const current = await opties();
    current.state.arabischeNamen = 'aan';
    current.state.godsnaamOPV = 'yhwh';
    assert.equal(current.transformOPV('De HEERE sprak tot Mozes'), 'YHWH sprak tot Musa');
});

test('het optiepaneel toont de keuze', () => {
    assert.match(lees('js/options-panel.js'), /\[data-option-summary="arabischeNamen"\]/);
    assert.match(lees('index.html'), /value="aan"> Arabisch, voor moslimlezers/);
});

test('de stamboom krijgt de naamkeuze mee', () => {
    const bron = lees('js/reading-genealogy.js');
    assert.match(bron, /namen=arabisch/);
    assert.match(bron, /ov:opties-gewijzigd/);
});

test('het woordvenster blijft klein', () => {
    const css = lees('css/opv.css');
    assert.match(css, /\.opw-word-dialog \{ width: min\(92vw, 420px\)/);
    assert.match(css, /\.opw-term-media img \{[^}]*max-height: 170px/);
});
