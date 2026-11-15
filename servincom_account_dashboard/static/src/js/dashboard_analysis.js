/** @odoo-module **/
// Copyright 2026 SERVINCOM SOLUCIONES, S.L.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";
import { formatFloat } from "@web/views/fields/formatters";

const MODEL = "servincom.account.dashboard";

export class MonthlySummary extends Component {
    static template = "servincom_account_dashboard.MonthlySummary";
    static props = { ...standardFieldProps };
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null });
        onWillStart(() => this.load());
    }
    async load() {
        this.state.data = await this.orm.call(MODEL, "get_monthly_summary", [], {
            context: this.props.record.context,
        });
    }
    amount(value) {
        return formatFloat(value, { digits: [16, this.state.data.digits] });
    }
    async drilldown(cell) {
        if (!cell.drilldown) {
            return;
        }
        const action = await this.orm.call("mis.report.instance", "drilldown", [
            this.state.data.instance_id, cell.drilldown,
        ], { context: { ...this.props.record.context, mis_pivot_date: `${this.state.data.year}-01-01` } });
        if (action) {
            await this.action.doAction(action);
        }
    }
}

registry.category("fields").add("servincom_monthly_summary", {
    component: MonthlySummary, supportedTypes: ["integer"],
});

export class DashboardAnalysis extends Component {
    static template = "servincom_account_dashboard.Analysis";
    static props = ["*"];
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null, year: null, endMonth: null, salesperson: "",
            loading: false, error: "", filter: "all", search: "", page: 0,
            showCurrent: true, showPrevious: true, sortKey: "current", sortDirection: "desc",
            salesScope: "comparable" });
        this.pageSize = 50;
        this.requestId = 0;
        onWillStart(() => this.load());
    }
    get customers() {
        return this.props.action.tag === "servincom_customer_evolution";
    }
    get title() {
        return this.customers ? _t("Customer evolution") : _t("Annual comparison");
    }
    async load() {
        const requestId = ++this.requestId;
        this.state.loading = true;
        this.state.error = "";
        try {
            const args = [this.state.year === null ? null : Number(this.state.year),
                this.state.endMonth === null ? null : Number(this.state.endMonth)];
            if (this.customers) {
                args.push(this.state.salesperson ? Number(this.state.salesperson) : null);
            }
            const data = await this.orm.call(MODEL,
                this.customers ? "get_customer_evolution" : "get_annual_comparison", args);
            if (requestId !== this.requestId) {
                return;
            }
            this.state.data = data;
            this.state.year = data.year;
            this.state.endMonth = data.end_month;
            this.state.page = 0;
        } catch (error) {
            if (requestId === this.requestId) {
                this.state.error = error.data?.message || _t("The report could not be loaded. Try again.");
                this.state.data = null;
            }
        } finally {
            if (requestId === this.requestId) {
                this.state.loading = false;
            }
        }
    }
    amount(value) {
        return value === null || value === undefined ? "—" : formatFloat(value,
            { digits: [16, this.state.data?.digits ?? 2] });
    }
    percent(value) {
        return value === null || value === undefined ? "—" : `${formatFloat(value, { digits: [16, 1] })} %`;
    }
    date(value) {
        return value ? value.split("-").reverse().join("/") : "—";
    }
    get cards() {
        const data = this.state.data;
        const counts = data.counts;
        if (!this.bothYears) {
            const key = this.state.showCurrent ? "current" : "previous";
            return [
                { key: "active", label: _t("Active customers"), value: data.period_counts[key], tone: "blue" },
                { key: "all", label: _t("Available net invoicing"), value: this.amount(data.sales.available[12][key]), tone: "green" },
            ];
        }
        return [
            { key: "active", label: _t("Active customers"), value: counts.active, tone: "blue" },
            { key: "decline", label: _t("Purchases down"), value: counts.decline, tone: "amber" },
            { key: "no_purchase", label: _t("No purchases in period"), value: counts.no_purchase, tone: "red" },
            this.state.data.matched_history
                ? { key: "unavailable", label: _t("No comparable data"), value: counts.unavailable, tone: "gray" }
                : { key: "new", label: _t("First recorded purchase"), value: counts.new, tone: "green" },
        ];
    }
    get bothYears() {
        return this.state.showCurrent && this.state.showPrevious;
    }
    get selectedPeriod() {
        return this.bothYears ? "both" : this.state.showCurrent ? "current" : "previous";
    }
    toggleYear(key) {
        // At least one year must remain visible.
        const other = key === "showCurrent" ? "showPrevious" : "showCurrent";
        if (this.state[key] && !this.state[other]) {
            return;
        }
        this.state[key] = !this.state[key];
        this.state.salesScope = this.bothYears ? "comparable" : "available";
        this.state.filter = "all";
        this.state.page = 0;
        if (!this.columns.some(column => column.key === this.state.sortKey)) {
            this.state.sortKey = this.state.showCurrent ? "current" : "previous";
            this.state.sortDirection = "desc";
        }
    }
    get columns() {
        const data = this.state.data;
        return [
            { key: "name", label: _t("Customer") },
            ...(this.state.showPrevious ? [{ key: "previous", label: data.previous_year }] : []),
            ...(this.state.showCurrent ? [{ key: "current", label: data.year }] : []),
            ...(this.bothYears ? [{ key: "delta", label: _t("Difference") },
                { key: "percent", label: _t("Change %") }] : []),
            { key: "last_purchase", label: _t("Last purchase") },
            ...(this.bothYears ? [{ key: "status_label", label: _t("Situation") }] : []),
        ];
    }
    lastPurchase(row) {
        return this.bothYears ? row.last_purchase : row[`last_purchase_${this.selectedPeriod}`];
    }
    sortAria(key) {
        return this.state.sortKey === key ? (this.state.sortDirection === "asc" ? "ascending" : "descending") : "none";
    }
    sortIcon(key) {
        return this.state.sortKey === key ? (this.state.sortDirection === "asc" ? "↑" : "↓") : "↕";
    }
    sortBy(key) {
        if (!this.columns.some(column => column.key === key)) {
            return;
        }
        this.state.sortDirection = this.state.sortKey === key
            ? (this.state.sortDirection === "asc" ? "desc" : "asc")
            : (["name", "status_label"].includes(key) ? "asc" : "desc");
        this.state.sortKey = key;
        this.state.page = 0;
    }
    get filteredRows() {
        const cacheKey = [this.state.data.rows, this.state.search, this.state.filter,
            this.state.showCurrent, this.state.showPrevious, this.state.sortKey, this.state.sortDirection];
        if (this.rowsCache?.key.every((value, index) => value === cacheKey[index])) {
            return this.rowsCache.rows;
        }
        const query = this.state.search.trim().toLocaleLowerCase();
        const period = this.selectedPeriod;
        const key = this.state.sortKey;
        const value = row => key === "last_purchase" ? this.lastPurchase(row) : row[key];
        const compare = (a, b) => typeof a === "number" && typeof b === "number" ? a - b
            : String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: "base" });
        const rows = this.state.data.rows.filter(row =>
            (this.bothYears || row[`has_${period}`]) &&
            (this.state.filter === "all" || (this.state.filter === "active" &&
                (period === "previous" ? row.previous_active : row.active)) ||
                (this.bothYears && row.status === this.state.filter)) &&
            (!query || row.name.toLocaleLowerCase().includes(query)))
            .sort((a, b) => {
                const av = value(a), bv = value(b);
                const missingA = av === null || av === undefined || av === "";
                const missingB = bv === null || bv === undefined || bv === "";
                if (missingA !== missingB) {
                    return missingA ? 1 : -1;
                }
                const order = missingA ? 0 : compare(av, bv);
                return (this.state.sortDirection === "asc" ? order : -order) ||
                    compare(a.name, b.name) || a.id - b.id;
            });
        this.rowsCache = { key: cacheKey, rows };
        return rows;
    }
    get pageCount() {
        return Math.ceil(this.filteredRows.length / this.pageSize);
    }
    get pageIndex() {
        return Math.max(0, Math.min(this.state.page, this.pageCount - 1));
    }
    get pageRows() {
        return this.filteredRows.slice(this.pageIndex * this.pageSize, (this.pageIndex + 1) * this.pageSize);
    }
    get pageRange() {
        const total = this.filteredRows.length;
        return _t("%s–%s of %s customers", total ? this.pageIndex * this.pageSize + 1 : 0,
            Math.min((this.pageIndex + 1) * this.pageSize, total), total);
    }
    setPage(page) {
        const number = Number(page);
        if (Number.isInteger(number)) {
            this.state.page = Math.max(0, Math.min(number, this.pageCount - 1));
        }
    }
    jumpPage(event) {
        const page = Number(event.target.value);
        if (Number.isFinite(page)) {
            this.setPage(Math.trunc(page) - 1);
        }
        event.target.value = this.pageCount ? this.pageIndex + 1 : 0;
    }
    setFilter(key) {
        this.state.filter = key;
        this.state.page = 0;
    }
    search(event) {
        this.state.search = event.target.value;
        this.state.page = 0;
    }
    canOpenDocuments(row, history) {
        const data = this.state.data;
        return ["current", "previous"].some(key =>
            (this.bothYears || this.selectedPeriod === key) && row[`has_${key}`] &&
            data.historical_years.includes(key === "current" ? data.year : data.previous_year) === history);
    }
    async openInvoices(row) {
        const data = this.state.data;
        const action = await this.orm.call(MODEL, "action_customer_invoices", [
            row.id, data.year, data.end_month, data.salesperson_id || null, this.selectedPeriod,
        ]);
        await this.action.doAction(action);
    }
    async openHistory(row) {
        const data = this.state.data;
        const action = await this.orm.call(MODEL, "action_customer_history", [
            row.id, data.year, data.end_month, data.salesperson_id || null, this.selectedPeriod,
        ]);
        await this.action.doAction(action);
    }
    get comparisonRows() {
        const data = this.state.data;
        return [...data.months, _t("Accumulated to cutoff")].map((label, index) => ({
            index, label, income: data.rows[0].cells[index], expense: data.rows[1].cells[index],
            result: data.rows[2].cells[index],
        }));
    }
    get customerTrend() {
        return this.bothYears ? this.state.data.trend : this.state.data.period_trend;
    }
    get salesRows() {
        const data = this.state.data;
        return data.sales[this.state.salesScope].map((row, index) => ({ ...row,
            label: index === 12 ? _t("Accumulated to cutoff") : data.months[index], index }));
    }
    get compareSales() {
        return this.bothYears && this.state.salesScope === "comparable";
    }
    get salesChart() {
        return this.makeChart(this.salesRows.slice(0, 12));
    }
    get chart() {
        return this.makeChart(this.customers ? this.customerTrend : this.state.data.rows[2].cells.slice(0, 12));
    }
    makeChart(values) {
        const keys = this.customers
            ? [ ...(this.state.showCurrent ? ["current"] : []), ...(this.state.showPrevious ? ["previous"] : []) ]
            : ["current", "previous"];
        const numbers = values.flatMap(row => keys.map(key => row[key])).filter(value => Number.isFinite(value));
        const min = Math.min(0, ...numbers);
        const max = Math.max(1, ...numbers);
        const y = value => 175 - (value - min) / (max - min) * 145;
        const points = key => !keys.includes(key) ? [] : values.map((row, index) => !Number.isFinite(row[key]) ? null :
            { x: 110 + index * 65, y: y(row[key]), value: row[key], index }).filter(Boolean);
        const current = points("current");
        const previous = points("previous");
        return { current, previous, currentLine: current.map(p => `${p.x},${p.y}`).join(" "),
            previousLine: previous.map(p => `${p.x},${p.y}`).join(" "),
            zero: y(0), max, min };
    }
}

registry.category("actions").add("servincom_annual_comparison", DashboardAnalysis);
registry.category("actions").add("servincom_customer_evolution", DashboardAnalysis);
