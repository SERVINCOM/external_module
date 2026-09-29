# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AeatVatBookMapLine(models.Model):
    _inherit = "aeat.vat.book.map.line"

    servincom_is_igic = fields.Boolean(string="IGIC mapping")

    def get_taxes_for_company(self, company):
        self.ensure_one()
        # OCA searches all book maps. Keep the two tax systems separate even
        # when no tax agency filter has been selected on the book.
        if self.servincom_is_igic != bool(self.env.context.get("servincom_igic_book")):
            return self.env["account.tax"]
        taxes = super().get_taxes_for_company(company)
        if self.servincom_is_igic:
            # Include archived equivalents used by historical posted invoices.
            tax_model = self.env["account.tax"].with_context(active_test=False)
            equivalent_domain = [("servincom_igic_equivalent_tax_id", "in", taxes.ids)]
            if "aeat_equivalent_tax_id" in tax_model._fields:
                equivalent_domain = (
                    ["|"]
                    + equivalent_domain
                    + [("aeat_equivalent_tax_id", "in", taxes.ids)]
                )
            taxes |= tax_model.search(
                [("company_id", "=", company.id)] + equivalent_domain
            )
            taxes = taxes.filtered(lambda tax: tax.company_id == company)
        return taxes
