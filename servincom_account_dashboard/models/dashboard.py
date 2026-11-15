# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
import ast
from datetime import date

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, ValidationError

GROUP = "servincom_account_dashboard.group_dashboard_reader"
MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


class AccountDashboard(models.Model):
    _name = "servincom.account.dashboard"
    _description = "Accounting Dashboard"
    _check_company_auto = True
    _rec_name = "company_id"

    company_id = fields.Many2one("res.company", string="Company", required=True, ondelete="cascade")
    summary_instance_id = fields.Many2one(
        "mis.report.instance", string="Summary report", required=True, check_company=True, ondelete="restrict",
    )
    detail_instance_id = fields.Many2one(
        "mis.report.instance", string="Detail report", required=True, check_company=True, ondelete="restrict",
    )
    year = fields.Integer(string="Year", required=True, default=lambda self: fields.Date.today().year)
    excluded_journal_ids = fields.Many2many(
        "account.journal", string="Excluded journals", check_company=True,
        help="Select opening and closing journals to exclude. Do not exclude POS sales journals.",
    )

    _sql_constraints = [
        ("company_unique", "unique(company_id)", "Only one dashboard is allowed per company."),
    ]

    @api.constrains("year", "summary_instance_id", "detail_instance_id", "company_id")
    def _check_configuration(self):
        for record in self:
            if not 1900 <= record.year <= 9998:
                raise ValidationError(self.env._("Choose a year between 1900 and 9998."))
            instances = record.summary_instance_id | record.detail_instance_id
            if len(instances) != 2 or any(
                instance.company_id != record.company_id
                or instance.multi_company or instance.company_ids
                or not instance.report_id.servincom_dashboard_report
                for instance in instances
            ):
                raise ValidationError(self.env._("Use two protected reports from the same company."))

    @api.model
    def _check_dashboard_access(self):
        if not self.env.su and not self.env.user.has_group(GROUP):
            raise AccessError(self.env._("You do not have access to accounting dashboards."))
        # Accessing env.company validates allowed_company_ids for non-superusers.
        return self.env.company

    @api.model
    def _ensure_company_dashboard(self):
        company = self._check_dashboard_access()
        dashboard = self.sudo().search([("company_id", "=", company.id)], limit=1)
        if dashboard:
            return dashboard.with_env(self.env)
        year = fields.Date.context_today(self).year
        instances = []
        for report_key, title in [
            ("report_summary", self.env._("Monthly results")),
            ("report_detail", self.env._("Account detail")),
        ]:
            report = self.env.ref("servincom_account_dashboard." + report_key)
            periods = [Command.create({
                "name": self.env._(month) + " " + str(year),
                "sequence": index + 1, "source": "actuals", "mode": "relative",
                "type": "m", "offset": index, "duration": 1,
            }) for index, month in enumerate(MONTHS)]
            periods.append(Command.create({
                "name": self.env._("Annual total") + " " + str(year),
                "sequence": 13, "source": "actuals", "mode": "relative",
                "type": "y", "offset": 0, "duration": 1,
            }))
            instances.append(self.env["mis.report.instance"].sudo().create({
                "name": "%s · %s" % (title, year), "report_id": report.id,
                "company_id": company.id, "currency_id": company.currency_id.id,
                "multi_company": False, "date": date(year, 1, 1),
                "target_move": "posted", "period_ids": periods,
                "landscape_pdf": True, "wide_display_by_default": True,
                "widget_show_filters": False, "widget_show_pivot_date": False,
                "widget_show_settings_button": False,
                "display_columns_description": False,
            }))
        dashboard = self.sudo().create({
            "company_id": company.id, "year": year,
            "summary_instance_id": instances[0].id, "detail_instance_id": instances[1].id,
        })
        return dashboard.with_env(self.env)

    def _set_year(self, year):
        self.ensure_one()
        company = self._check_dashboard_access()
        self.check_access("read")
        if self.company_id != company:
            raise AccessError(self.env._("Open the dashboard for the active company."))
        if not isinstance(year, int) or isinstance(year, bool) or not 1900 <= year <= 9998:
            raise ValidationError(self.env._("Choose a year between 1900 and 9998."))
        # Narrow elevation: change only this company's report dates/labels, never
        # formulas, company scope, journal filters, accounting entries or users.
        self.sudo().write({"year": year})
        for instance, title in [
            (self.summary_instance_id, self.env._("Monthly results")),
            (self.detail_instance_id, self.env._("Account detail")),
        ]:
            instance.sudo().write({"date": date(year, 1, 1), "name": "%s · %s" % (title, year)})
            for period in instance.period_ids:
                label = self.env._("Annual total") if period.type == "y" else self.env._(MONTHS[period.offset])
                period.sudo().write({"name": "%s %s" % (label, year)})

    def action_apply_journals(self):
        self.ensure_one()
        self.check_access("write")
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(self.env._("Only settings administrators can configure the dashboard."))
        for instance in self.summary_instance_id | self.detail_instance_id:
            # Keep any additional domain adopted from an existing installation.
            existing = ast.literal_eval(instance.analytic_domain or "[]")
            domain = [term for term in existing if not (
                isinstance(term, (tuple, list)) and len(term) == 3
                and term[0] == "journal_id" and term[1] == "not in"
            )]
            # Non-conjunctive domains cannot be safely edited automatically.
            if any(isinstance(term, str) for term in existing):
                raise ValidationError(self.env._("Review the report domain before changing excluded journals."))
            if self.excluded_journal_ids:
                domain.append(("journal_id", "not in", self.excluded_journal_ids.ids))
            instance.sudo().write({"analytic_domain": repr(domain)})
        return {"type": "ir.actions.client", "tag": "reload"}

    @api.model
    def action_open(self):
        self._ensure_company_dashboard()
        return self.env["ir.actions.actions"]._for_xml_id("servincom_account_dashboard.action_board")

    @api.model
    def action_choose_year(self):
        dashboard = self._ensure_company_dashboard()
        action = self.env["ir.actions.actions"]._for_xml_id("servincom_account_dashboard.action_year")
        action["context"] = dict(self.env.context, default_year=dashboard.year)
        return action
