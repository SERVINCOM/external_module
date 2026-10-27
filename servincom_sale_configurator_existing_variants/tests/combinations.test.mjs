import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {test} from 'node:test';
const source = await readFile(new URL('../static/src/js/combinations.js', import.meta.url),'utf8');
const {normalizeSelection, updateVisibility, hasExistingSelection} = await import(
    `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
);
function fixture() {
    return {
        attribute_lines: [
            {id: 1, create_variant:'always', attribute_values:[{id:1},{id:2}], selected_attribute_value_ids:[1]},
            {id: 2, create_variant:'always', attribute_values:[10,20,30,40,50,60,70].map(id=>({id})), selected_attribute_value_ids:[10]},
            {id: 3, create_variant:'no_variant', attribute_values:[{id:99}], selected_attribute_value_ids:[99]},
        ],
        servincom_combinations:[[1,10],[1,20],[1,30],[1,50],[1,70],[2,40],[2,60]],
        exclusions:{}, parent_exclusions:{},
    };
}
const visible=(p,index)=>p.attribute_lines[index].attribute_values.filter(v=>!v.servincomHidden).map(v=>v.id);
test('first type shows five capacities while both types stay accessible',()=>{
    const p=fixture(); updateVisibility(p);
    assert.deepEqual(visible(p,0),[1,2]);
    assert.deepEqual(visible(p,1),[10,20,30,50,70]);
    assert.ok(hasExistingSelection(p));
});
test('switch to second type selects a valid capacity and switching back remains possible',()=>{
    const p=fixture();p.attribute_lines[0].selected_attribute_value_ids=[2];
    assert.ok(normalizeSelection(p));updateVisibility(p);
    assert.deepEqual(visible(p,1),[40,60]);
    assert.deepEqual(p.attribute_lines[1].selected_attribute_value_ids,[40]);
    assert.deepEqual(visible(p,0),[1,2]);assert.ok(hasExistingSelection(p));
    p.attribute_lines[0].selected_attribute_value_ids=[1];normalizeSelection(p);updateVisibility(p);
    assert.deepEqual(visible(p,1),[10,20,30,50,70]);assert.ok(hasExistingSelection(p));
});
test('keeps an existing selection and rejects deleted combinations',()=>{
    const p=fixture();p.attribute_lines[1].selected_attribute_value_ids=[70];
    assert.equal(normalizeSelection(p),false);
    p.attribute_lines[1].selected_attribute_value_ids=[40];
    assert.equal(hasExistingSelection(p),false);
});
test('parent and informational exclusions are respected',()=>{
    const p=fixture();p.parent_exclusions={900:[10,20]};p.exclusions={99:[30]};
    normalizeSelection(p,[900]);updateVisibility(p,[900]);
    assert.deepEqual(visible(p,1),[50,70]);
    assert.deepEqual(p.attribute_lines[1].selected_attribute_value_ids,[50]);
    assert.equal(p.attribute_lines[2].attribute_values[0].servincomHidden,undefined);
});
test('empty matrix offers no choices and cannot be confirmed',()=>{
    const p=fixture();p.servincom_combinations=[];normalizeSelection(p);updateVisibility(p);
    assert.deepEqual(visible(p,0),[]);assert.equal(hasExistingSelection(p),false);
});
test('three attribute levels keep later choices dependent on the full prefix',()=>{
    const p=fixture();p.attribute_lines.splice(2,0,{id:4,create_variant:'always',attribute_values:[{id:80},{id:81}],selected_attribute_value_ids:[81]});
    p.servincom_combinations=[[1,10,80],[1,20,81],[2,40,81]];
    normalizeSelection(p);updateVisibility(p);
    assert.deepEqual(visible(p,2),[80]);assert.ok(hasExistingSelection(p));
});
