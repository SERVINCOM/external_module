# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountTax(models.Model):
    _inherit = "account.tax"

    servincom_igic_deductible_percent = fields.Float(
        string="IGIC deductible percentage",
        default=100.0,
        help="Percentage of the posted IGIC fee deductible in the IGIC book. "
        "Use 0 for non-deductible IGIC. This does not change accounting entries.",
    )

    @api.constrains("servincom_igic_deductible_percent")
    def _check_igic_deductible_percent(self):
        for tax in self:
            if not 0 <= tax.servincom_igic_deductible_percent <= 100:
                raise ValidationError(
                    self.env._(
                        "The IGIC deductible percentage must be between 0 and 100."
                    )
                )
