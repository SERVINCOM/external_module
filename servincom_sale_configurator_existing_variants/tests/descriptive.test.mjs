import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFile } from 'node:fs/promises';
const source = await readFile(new URL('../static/src/js/descriptive.js', import.meta.url), 'utf8');
const { isDescriptive, clearDescriptiveSelections } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const line = (id, mode='no_variant') => ({id, create_variant:mode, selected_attribute_value_ids:[id*10]});
test('clears all descriptive selections, retains size and commercial extras', () => {
 const p={servincom_descriptive_line_ids:[1,2],attribute_lines:[line(1),line(2),line(3,'always'),line(4)]};
 assert.equal(clearDescriptiveSelections(p),true);
 assert.deepEqual(p.attribute_lines.map(l=>l.selected_attribute_value_ids),[[],[],[30],[40]]);
 assert.equal(clearDescriptiveSelections(p),false);
});
test('no metadata preserves native choices',()=>{
 const p={attribute_lines:[line(1)]};assert.equal(clearDescriptiveSelections(p),false);
 assert.equal(isDescriptive(p,p.attribute_lines[0]),false);
});
test('variant-generating attributes cannot be hidden by metadata',()=>{
 const p={servincom_descriptive_line_ids:[1],attribute_lines:[line(1,'dynamic')]};
 assert.equal(clearDescriptiveSelections(p),false);
});
