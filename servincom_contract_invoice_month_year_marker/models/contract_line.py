from odoo import models
from odoo.tools import format_date


class ContractLine(models.Model):
    _inherit = "contract.line"

    def _insert_markers(self, first_date_invoiced, last_date_invoiced):
        self.ensure_one()
        name = super()._insert_markers(first_date_invoiced, last_date_invoiced)

        lang_code = self.contract_id.partner_id.lang or self.env.user.lang or "es_ES"
        month_name = format_date(
            self.env,
            first_date_invoiced,
            lang_code=lang_code,
            date_format="MMMM",
        )
        year = format_date(
            self.env,
            first_date_invoiced,
            lang_code=lang_code,
            date_format="y",
        )
        month_year = f"{month_name} {year}"

        return name.replace("#INVOICEMONTHYEAR#", month_year)
