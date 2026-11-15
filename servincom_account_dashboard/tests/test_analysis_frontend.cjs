// Copyright 2026 SERVINCOM SOLUCIONES, S.L.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
// Standalone component-logic checks: node tests/test_analysis_frontend.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../static/src/js/dashboard_analysis.js'), 'utf8')
    .replace(/^import .*;$/gm, '').replace(/export class /g, 'class ');
const sandbox = {
    Component: class {}, onWillStart() {}, useState: value => value,
    registry: {category: () => ({add() {}})}, standardFieldProps: {},
    _t: (text, ...args) => { let i = 0; return text.replace(/%s/g, () => args[i++]); },
    formatFloat: value => String(value), useService() {},
};
vm.createContext(sandbox);
vm.runInContext(source + '\nthis.Analysis = DashboardAnalysis;', sandbox);
const component = Object.create(sandbox.Analysis.prototype);
const points = Array.from({length: 12}, (_, i) => ({month: i + 1,
    current: i ? null : 1, previous: i ? null : 2}));
component.state = {filter: 'all', search: '', page: 0, showCurrent: true, showPrevious: true,
    sortKey: 'current', sortDirection: 'desc', salesScope: 'comparable',
    collapsedPanels: {sales: false, customers: false, result: false},
    chartVisibility: {sales: {current: true, previous: true},
        customers: {current: true, previous: true}, result: {current: true, previous: true}}, data: {
    year: 2026, previous_year: 2025, end_month: 1, salesperson_id: 7, historical_years: [2025],
    matched_history: true, digits: 2, counts: {active: 2, decline: 1, no_purchase: 1, new: 0, unavailable: 1},
    period_counts: {current: 2, previous: 2}, trend: points,
    period_trend: points.map(p => ({...p, current: p.current === null ? null : 2})),
    months: Array.from({length: 12}, (_, i) => String(i + 1)),
    sales: {comparable: [...points, {current: 80, previous: 140}], available: [...points, {current: 100, previous: 140}]},
    rows: [
        {id: 1, name: 'Verified', active: true, previous_active: true, status: 'decline',
            previous: 100, current: 80, delta: -20, percent: -20, has_current: true, has_previous: true,
            last_purchase: '2026-01-12', last_purchase_current: '2026-01-12', last_purchase_previous: '2025-01-10'},
        {id: 2, name: 'Unmatched', active: true, status: 'unavailable', previous: null,
            current: 20, delta: null, percent: null, has_current: true, has_previous: false,
            last_purchase: '2026-01-15', last_purchase_current: '2026-01-15'},
        {id: 3, name: 'Lapsed', active: false, previous_active: true, status: 'no_purchase',
            previous: 40, current: 0, delta: -40, percent: -100, has_current: false, has_previous: true,
            last_purchase: '2025-01-09', last_purchase_previous: '2025-01-09'},
    ],
}};
component.props = {action: {tag: 'servincom_customer_evolution'}};
component.pageSize = 2;
const ids = () => Array.from(component.filteredRows, row => row.id);
assert.equal(component.amount(null), '—');
assert.equal(component.cards[3].key, 'unavailable');
assert.deepEqual(ids(), [1, 2, 3]);
for (const key of ['previous', 'percent', 'delta']) {
    component.sortBy(key);
    assert.equal(ids().at(-1), 2, 'Missing amounts must remain last descending');
    component.sortBy(key);
    assert.equal(ids().at(-1), 2, 'Missing amounts must remain last ascending');
}
component.sortBy('last_purchase');
assert.deepEqual(ids(), [2, 1, 3]);
component.sortBy('last_purchase');
assert.deepEqual(ids(), [3, 1, 2]);
component.sortBy('current');
assert.equal(component.pageCount, 2);
assert.equal(component.pageRange, '1–2 of 3 customers');
component.movePage(-1);
assert.equal(component.pageIndex, 1, 'Previous from the first page wraps to the last');
component.movePage(1);
assert.equal(component.pageIndex, 0, 'Next from the last page wraps to the first');
component.movePage(1);
assert.equal(component.pageIndex, 1);
component.movePage(-1);
assert.equal(component.pageIndex, 0);
component.setPage(999);
assert.equal(component.pageIndex, 1);
assert.equal(component.pageRows.length, 1);
assert.equal(component.pageRange, '3–3 of 3 customers');
const jump = {target: {value: '999'}};
component.jumpPage(jump);
assert.equal(jump.target.value, 2);
component.setPage(-9);
assert.equal(component.pageIndex, 0);
component.setFilter('unavailable');
assert.deepEqual(ids(), [2]);
component.movePage(-1);
assert.equal(component.pageIndex, 0, 'A single page remains stable');
component.search({target: {value: 'no match'}});
assert.equal(component.pageCount, 0);
assert.equal(component.pageRange, '0–0 of 0 customers');
component.movePage(-1);
component.movePage(1);
assert.equal(component.state.page, 0, 'Empty results do not produce NaN or negative pages');
component.search({target: {value: ''}});
component.setFilter('all');
component.toggleChartYear('sales', 'previous');
assert.equal(component.salesChart.previous.length, 0);
assert.equal(component.salesChart.current.length, 1);
assert.equal(component.chart.previous.length, 1, 'Customer chart is independent');
assert.equal(component.bothYears, true, 'Legend buttons do not change report scope');
assert.equal(component.salesRows[0].previous, 2, 'Legend buttons do not change table data');
component.toggleChartYear('sales', 'current');
assert.equal(component.salesChart.hasVisibleSeries, false);
component.toggleChartYear('customers', 'current');
assert.equal(component.chart.current.length, 0);
assert.equal(component.chart.previous.length, 1);
component.togglePanel('sales');
assert.equal(component.state.collapsedPanels.sales, true);
assert.equal(component.state.collapsedPanels.customers, false);
component.togglePanel('sales');
assert.equal(component.state.collapsedPanels.sales, false);
assert.equal(component.salesChart.hasVisibleSeries, false, 'Collapsing keeps the legend choice');
component.toggleChartYear('sales', 'previous');
component.toggleChartYear('sales', 'current');
component.toggleChartYear('customers', 'current');
component.toggleYear('showCurrent');
assert.equal(component.selectedPeriod, 'previous');
assert.equal(component.state.salesScope, 'available');
assert.equal(component.cards.length, 2);
assert.equal(component.cards[0].value, 2);
assert.equal(component.columns.some(c => c.key === 'percent'), false);
assert.deepEqual(new Set(ids()), new Set([1, 3]));
assert.equal(component.lastPurchase(component.state.data.rows[0]), '2025-01-10');
assert.equal(component.chart.current.length, 0);
assert.equal(component.canOpenDocuments(component.state.data.rows[0], true), true);
assert.equal(component.canOpenDocuments(component.state.data.rows[0], false), false);
component.toggleYear('showPrevious'); // Cannot hide the only visible year.
assert.equal(component.selectedPeriod, 'previous');
component.toggleYear('showCurrent');
assert.equal(component.selectedPeriod, 'both');
component.toggleYear('showPrevious');
assert.equal(component.selectedPeriod, 'current');
assert.deepEqual(new Set(ids()), new Set([1, 2]));
assert.equal(component.chart.current[0].value, 2);
assert.equal(component.chart.previous.length, 0);
assert.equal(component.canOpenDocuments(component.state.data.rows[0], true), false);
assert.equal(component.canOpenDocuments(component.state.data.rows[0], false), true);
component.state.data.trend.forEach(point => {point.current = null; point.previous = null;});
component.toggleYear('showPrevious');
assert.equal(component.chart.currentLine, '');
assert.equal(component.chart.previousLine, '');
const calls = [];
component.orm = {call: async (...args) => { calls.push(args); return {type: 'test'}; }};
component.action = {doAction: async () => {}};
(async () => {
    component.toggleYear('showCurrent');
    await component.openHistory({id: 1});
    assert.deepEqual(Array.from(calls[0][2]), [1, 2026, 1, 7, 'previous']);
    component.toggleYear('showCurrent');
    component.toggleYear('showPrevious');
    await component.openInvoices({id: 1});
    assert.deepEqual(Array.from(calls[1][2]), [1, 2026, 1, 7, 'current']);
    console.log('PASS: sorting, missing values, circular pagination, independent chart legends and panels, year scope and drilldown periods.');
})().catch(error => { console.error(error); process.exitCode = 1; });
