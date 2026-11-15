# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from datetime import date
from numbers import Real

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.mis_builder.models.accounting_none import AccountingNone

from .dashboard import MONTHS


class DashboardAnalysis(models.Model):
    _inherit = "servincom.account.dashboard"

    def _analysis_metadata(self):
        self.ensure_one()
        self._check_dashboard_access()
        self.check_access("read")
        return {
            "company": self.company_id.display_name,
            "currency": self.company_id.currency_id.name,
            "digits": self.company_id.currency_id.decimal_places,
            "months": [self.env._(month) for month in MONTHS],
        }

    @api.model
    def _analysis_period(self, year, end_month=None):
        today = fields.Date.context_today(self)
        year = today.year if year is None else year
        if type(year) is not int or not 1901 <= year <= 9998:
            raise ValidationError(self.env._("Choose a comparison year between 1901 and 9998."))
        end_month = (today.month if year == today.year else 12) if end_month is None else end_month
        if type(end_month) is not int or not 1 <= end_month <= 12:
            raise ValidationError(self.env._("Choose a month between 1 and 12."))
        start = date(year, 1, 1)
        end = date(year, end_month, 1) + relativedelta(day=31)
        end = min(end, today) if year == today.year else end
        return start, end, start - relativedelta(years=1), end - relativedelta(years=1)

    def _monthly_snapshot(self, year, cutoff=None):
        """Read the three real MIS totals, with the installed formulas/domains.

        MIS supports mis_pivot_date. Explicitly invalidate its computed dates
        because some 18.0 revisions do not declare depends_context on them.
        No instance, period, saved year, formula or accounting entry is written.
        """
        self.ensure_one()
        self._check_dashboard_access()
        self.check_access("read")
        instance = self.summary_instance_id
        instance.check_access("read")
        periods = instance.period_ids
        periods.check_access("read")
        months = periods.filtered(lambda p: p.type == "m").sorted("offset")
        total = periods.filtered(lambda p: p.type == "y")
        if (len(months) != 12 or months.mapped("offset") != list(range(12))
                or len(total) != 1 or total.offset != 0 or len(periods) != 13
                or any(p.source != "actuals" or p.mode != "relative" or p.duration != 1 for p in periods)):
            raise ValidationError(self.env._("The summary requires twelve calendar months and one annual total."))
        context = dict(self.env.context, mis_pivot_date=date(year, 1, 1))
        # Start from the report's configured filters, not an unrelated action's
        # transient analytic search context.
        context["mis_analytic_domain"] = [("date", "<=", cutoff)] if cutoff else []
        report = instance.with_context(context)
        report.invalidate_recordset(["pivot_date"])
        report.period_ids.invalidate_recordset(["date_from", "date_to", "valid"])
        labels = {
            "income_total": self.env._("Income"),
            "expenses_total": self.env._("Purchases and expenses"),
            "monthly_result": self.env._("Result"),
        }
        try:
            matrix = report._compute_matrix()
            cols = {col.key: col for col in matrix.iter_cols()}
            rows = {}
            for row in matrix.iter_rows():
                if row.account_id or row.kpi.name not in labels:
                    continue
                cells = []
                for period in months | total:
                    values = list(cols[period.id].get_cell_tuple_for_row(row))
                    if len(values) != 1:
                        raise ValidationError(self.env._("The summary requires one value per indicator and month."))
                    cell = values[0]
                    value = cell.val
                    # MIS AccountingNone represents no movement. Errors must
                    # never be silently presented as a valid zero.
                    if value is AccountingNone:
                        value = 0.0
                    if not isinstance(value, Real):
                        raise ValidationError(self.env._("Review the MIS formula error before using the summary."))
                    cells.append({"value": float(value), "drilldown": cell.drilldown_arg})
                rows[row.kpi.name] = {"key": row.kpi.name, "label": labels[row.kpi.name], "cells": cells}
            if set(rows) != set(labels):
                raise ValidationError(self.env._("The MIS report must contain income_total, expenses_total and monthly_result."))
            return [rows[key] for key in labels]
        finally:
            report.invalidate_recordset(["pivot_date"])
            report.period_ids.invalidate_recordset(["date_from", "date_to", "valid"])

    @api.model
    def get_monthly_summary(self):
        dashboard = self._ensure_company_dashboard()
        return dict(dashboard._analysis_metadata(), year=dashboard.year,
                    instance_id=dashboard.summary_instance_id.id,
                    rows=dashboard._monthly_snapshot(dashboard.year))

    @api.model
    def get_annual_comparison(self, year=None, end_month=None):
        dashboard = self._ensure_company_dashboard()
        today = fields.Date.context_today(self)
        year = max(today.year, dashboard.comparison_start_year) if year is None else year
        start, end, previous_start, previous_end = self._analysis_period(year, end_month)
        result = dict(dashboard._analysis_metadata(), year=year, previous_year=year - 1,
                      end_month=end.month, cutoff=str(end), previous_cutoff=str(previous_end),
                      start_year=dashboard.comparison_start_year, rows=[], ready=False)
        if year < dashboard.comparison_start_year or start > today:
            result["message"] = self.env._("Comparison will be available from %s, using the previous year as its baseline.", dashboard.comparison_start_year)
            return result
        instance = dashboard.summary_instance_id
        base_domain = instance._get_filter_domain("account.move.line") + [
            ("company_id", "=", dashboard.company_id.id),
            "|", ("account_id.code", "=like", "6%"), ("account_id.code", "=like", "7%"),
        ]
        aml = self.env["account.move.line"]
        for begin, finish in [(start, end), (previous_start, previous_end)]:
            if not aml.search_count(base_domain + [("date", ">=", begin), ("date", "<=", finish)], limit=1):
                result["message"] = self.env._("There are no visible accounting entries in one of the periods. Review the baseline before comparing.")
                return result
        current = dashboard._monthly_snapshot(year, end)
        previous = dashboard._monthly_snapshot(year - 1, previous_end)
        for new, old in zip(current, previous):
            pairs = []
            for index, (new_cell, old_cell) in enumerate(zip(new["cells"], old["cells"])):
                a, b = new_cell["value"], old_cell["value"]
                visible = index < end.month or index == 12
                pairs.append({"current": a if visible else None, "previous": b if visible else None,
                              "delta": a - b if visible else None,
                              "percent": (a - b) / b * 100 if visible and b > 0 else None})
            result["rows"].append({"key": new["key"], "label": new["label"], "cells": pairs})
        result.update(ready=True, message=self.env._("Both years use the same cutoff. Check that the baseline is complete; absence of entries is not proof of completeness."))
        return result

    @api.model
    def _customer_domain(self, salesperson_id=None):
        company = self._check_dashboard_access()
        domain = [("company_id", "=", company.id), ("state", "=", "posted"),
                  ("move_type", "in", ["out_invoice", "out_refund"]), ("commercial_partner_id", "!=", False)]
        if salesperson_id:
            if type(salesperson_id) is not int or salesperson_id < 1:
                raise ValidationError(self.env._("Choose a valid salesperson."))
            domain.append(("invoice_user_id", "=", salesperson_id))
        return domain

    @api.model
    def get_customer_evolution(self, year=None, end_month=None, salesperson_id=None):
        company = self._check_dashboard_access()
        start, end, previous_start, previous_end = self._analysis_period(year, end_month)
        move = self.env["account.move"]
        base = self._customer_domain(salesperson_id)
        metadata = self._ensure_company_dashboard()._analysis_metadata()
        result = dict(metadata, year=start.year, previous_year=previous_start.year,
                      end_month=end.month, cutoff=str(end), previous_cutoff=str(previous_end),
                      salesperson_id=salesperson_id or False,
                      rows=[], trend=[], counts={"active": 0, "decline": 0, "no_purchase": 0, "new": 0},
                      salespeople=[], ready=start <= fields.Date.context_today(self))
        if not result["ready"]:
            return result
        # Read only aggregate invoice headers through the current user's ORM.
        # Company-currency signed untaxed totals already reverse credit notes.
        period_data = []
        for begin, finish in [(start, end), (previous_start, previous_end)]:
            domain = base + [("invoice_date", ">=", begin), ("invoice_date", "<=", finish)]
            totals = {partner.id: amount for partner, amount in move._read_group(
                domain, ["commercial_partner_id"], ["amount_untaxed_signed:sum"])}
            purchases = move._read_group(
                domain + [("move_type", "=", "out_invoice"), ("amount_total_signed", ">", 0)],
                ["commercial_partner_id", "invoice_date:month"], ["__count"],
            )
            buyers = {partner.id for partner, month, count in purchases}
            monthly = {month: set() for month in range(1, 13)}
            for partner, month, count in purchases:
                monthly[month.month].add(partner.id)
            period_data.append((totals, buyers, monthly))
        current, current_buyers, current_monthly = period_data[0]
        previous, previous_buyers, previous_monthly = period_data[1]
        # Respect partner rules as well: do not reveal a restricted partner's
        # name or its aggregate through the analysis endpoint.
        partners = self.env["res.partner"].with_context(active_test=False).search([
            ("id", "in", list(set(current) | set(previous))),
        ])
        visible = set(partners.ids)
        current_buyers &= visible
        previous_buyers &= visible
        history = {partner.id: (first, last) for partner, first, last in move._read_group(
            self._customer_domain() + [("commercial_partner_id", "in", partners.ids),
                                      ("move_type", "=", "out_invoice"), ("amount_total_signed", ">", 0),
                                      ("invoice_date", "<=", end)],
            ["commercial_partner_id"], ["invoice_date:min", "invoice_date:max"],
        )}
        labels = {
            "decline": self.env._("Purchases down"), "no_purchase": self.env._("No purchases in period"),
            "new": self.env._("First recorded purchase"), "recovered": self.env._("Buying again"),
            "growth": self.env._("Purchases up"), "stable": self.env._("Unchanged"),
            "credits": self.env._("Credit notes only"),
        }
        for partner in partners:
            a, b = current.get(partner.id, 0.0), previous.get(partner.id, 0.0)
            first, last = history.get(partner.id, (None, None))
            if partner.id in current_buyers:
                if first and first >= start:
                    status = "new"
                elif partner.id not in previous_buyers:
                    status = "recovered"
                else:
                    change = company.currency_id.compare_amounts(a, b)
                    status = "decline" if change < 0 else "growth" if change > 0 else "stable"
            else:
                status = "no_purchase" if partner.id in previous_buyers else "credits"
            result["rows"].append({"id": partner.id, "name": partner.display_name,
                                   "active": partner.id in current_buyers,
                                   "current": a, "previous": b, "delta": a - b,
                                   "percent": (a - b) / b * 100 if b > 0 else None,
                                   "last_purchase": str(last) if last else None,
                                   "status": status, "status_label": labels[status]})
        result["rows"].sort(key=lambda row: (row["delta"], row["name"].casefold()))
        result["counts"] = {"active": len(current_buyers), **{
            status: sum(row["status"] == status for row in result["rows"])
            for status in ["decline", "no_purchase", "new"]}}
        result["trend"] = [{"month": month, "current": len(current_monthly[month] & visible) if month <= end.month else None,
                            "previous": len(previous_monthly[month] & visible) if month <= end.month else None}
                           for month in range(1, 13)]
        salespeople = [user for user, in move._read_group(
            self._customer_domain() + [("invoice_date", ">=", previous_start), ("invoice_date", "<=", end)],
            ["invoice_user_id"], [],
        ) if user]
        # Archived salespeople still identify historical invoices. Keep them
        # selectable, after active users, without changing invoice assignments.
        result["salespeople"] = [{
            "id": user.id,
            "name": user.display_name if user.active else self.env._("%s (Archived)", user.display_name),
            "active": user.active,
        } for user in sorted(salespeople, key=lambda user: (
            not user.active, user.display_name.casefold(), user.id,
        ))]
        return result

    @api.model
    def action_customer_invoices(self, partner_id, year=None, end_month=None, salesperson_id=None):
        self._check_dashboard_access()
        start, end, previous_start, previous_end = self._analysis_period(year, end_month)
        partner = self.env["res.partner"].browse(partner_id).exists()
        partner.ensure_one()
        partner.check_access("read")
        domain = self._customer_domain(salesperson_id) + [("commercial_partner_id", "=", partner.id), "|",
                 "&", ("invoice_date", ">=", start), ("invoice_date", "<=", end),
                 "&", ("invoice_date", ">=", previous_start), ("invoice_date", "<=", previous_end)]
        return {"type": "ir.actions.act_window", "name": self.env._("Customer invoices"),
                "res_model": "account.move", "views": [(False, "list"), (False, "form")],
                "domain": domain, "context": dict(self.env.context, create=False)}
