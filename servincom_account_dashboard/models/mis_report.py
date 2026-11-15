# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from odoo import api, fields, models
from odoo.exceptions import AccessError


class MisReport(models.Model):
    _inherit = "mis.report"

    servincom_dashboard_report = fields.Boolean(
        string="Protected accounting dashboard", default=False,
        copy=False,
    )

    def _check_dashboard_flag(self, values):
        if "servincom_dashboard_report" in values and not (
            self.env.su or self.env.user.has_group("base.group_system")
        ):
            raise AccessError(self.env._("Only settings administrators can change report protection."))

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            self._check_dashboard_flag(values)
        return super().create(values_list)

    def write(self, values):
        self._check_dashboard_flag(values)
        return super().write(values)
