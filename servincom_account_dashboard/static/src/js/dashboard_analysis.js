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
            loading: false, error: "", filter: "all", search: "", page: 0 });
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
        const counts = this.state.data.counts;
        return [
            { key: "active", label: _t("Active customers"), value: counts.active, tone: "blue" },
            { key: "decline", label: _t("Purchases down"), value: counts.decline, tone: "amber" },
            { key: "no_purchase", label: _t("No purchases in period"), value: counts.no_purchase, tone: "red" },
            this.state.data.matched_history
                ? { key: "unavailable", label: _t("No comparable data"), value: counts.unavailable, tone: "gray" }
                : { key: "new", label: _t("First recorded purchase"), value: counts.new, tone: "green" },
        ];
    }
    get filteredRows() {
        const query = this.state.search.trim().toLocaleLowerCase();
        return this.state.data.rows.filter(row =>
            (this.state.filter === "all" || (this.state.filter === "active" && row.active) || row.status === this.state.filter) &&
            (!query || row.name.toLocaleLowerCase().includes(query)));
    }
    get pageRows() {
        return this.filteredRows.slice(this.state.page * this.pageSize, (this.state.page + 1) * this.pageSize);
    }
    setFilter(key) {
        this.state.filter = key;
        this.state.page = 0;
    }
    search(event) {
        this.state.search = event.target.value;
        this.state.page = 0;
    }
    async openInvoices(row) {
        const data = this.state.data;
        const action = await this.orm.call(MODEL, "action_customer_invoices", [
            row.id, data.year, data.end_month, data.salesperson_id || null,
        ]);
        await this.action.doAction(action);
    }
    async openHistory(row) {
        const data = this.state.data;
        const action = await this.orm.call(MODEL, "action_customer_history", [
            row.id, data.year, data.end_month, data.salesperson_id || null,
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
    get chart() {
        const data = this.state.data;
        const values = this.customers ? data.trend : data.rows[2].cells.slice(0, 12);
        const numbers = values.flatMap(row => [row.current, row.previous]).filter(value => value !== null);
        const min = Math.min(0, ...numbers);
        const max = Math.max(1, ...numbers);
        const y = value => 175 - (value - min) / (max - min) * 145;
        const points = key => values.map((row, index) => row[key] === null ? null :
            { x: 48 + index * 71, y: y(row[key]), value: row[key], index }).filter(Boolean);
        const current = points("current");
        const previous = points("previous");
        return { current, previous, currentLine: current.map(p => `${p.x},${p.y}`).join(" "),
            previousLine: previous.map(p => `${p.x},${p.y}`).join(" "),
            zero: y(0), max, min };
    }
}

registry.category("actions").add("servincom_annual_comparison", DashboardAnalysis);
registry.category("actions").add("servincom_customer_evolution", DashboardAnalysis);
