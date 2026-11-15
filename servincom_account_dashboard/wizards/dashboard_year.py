# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from odoo import fields, models


class DashboardYear(models.TransientModel):
    _name = "servincom.account.dashboard.year"
    _description = "Choose Dashboard Year"

    year = fields.Integer(string="Year", required=True, default=lambda self: fields.Date.today().year)

    def action_apply(self):
        self.ensure_one()
        self.check_access("read")
        dashboard = self.env["servincom.account.dashboard"]._ensure_company_dashboard()
        dashboard._set_year(self.year)
        action = dashboard.action_open()
        action["target"] = "main"
        return action
