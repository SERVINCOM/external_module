from odoo import models
from odoo.tools import format_date


INVOICE_MONTH_NAME_MARKER = "#INVOICEMONTHNAME#"
INVOICE_MONTH_YEAR_MARKER = "#INVOICEMONTHYEAR#"
INVOICE_YEAR_MARKER = "#YEAR#"
INVOICE_DATE_MARKERS = (
    INVOICE_MONTH_NAME_MARKER,
    INVOICE_MONTH_YEAR_MARKER,
    INVOICE_YEAR_MARKER,
)


class ContractLine(models.Model):
    _inherit = "contract.line"

    def _insert_markers(self, first_date_invoiced, last_date_invoiced):
        self.ensure_one()
        original_name = self.name or ""
        name = super()._insert_markers(first_date_invoiced, last_date_invoiced) or ""
        has_invoice_date_marker = any(
            marker in original_name for marker in INVOICE_DATE_MARKERS
        )
        if not first_date_invoiced or not has_invoice_date_marker:
            return name

        lang_code = self.contract_id.partner_id.lang or self.env.user.lang or "en_US"
        base_month_name = format_date(
            self.env,
            first_date_invoiced,
            lang_code=lang_code,
            date_format="MMMM",
        )
        month_name = base_month_name.upper()
        year = format_date(
            self.env,
            first_date_invoiced,
            lang_code=lang_code,
            date_format="y",
        )
        month_year = f"{month_name} {year}"

        if INVOICE_MONTH_NAME_MARKER in original_name:
            name = name.replace(
                base_month_name,
                month_name,
                original_name.count(INVOICE_MONTH_NAME_MARKER),
            )

        return (
            name.replace(INVOICE_MONTH_NAME_MARKER, month_name)
            .replace(INVOICE_MONTH_YEAR_MARKER, month_year)
            .replace(INVOICE_YEAR_MARKER, year)
        )
