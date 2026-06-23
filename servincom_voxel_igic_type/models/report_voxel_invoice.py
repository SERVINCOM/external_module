# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ReportVoxelInvoice(models.AbstractModel):
    _inherit = "report.edi_voxel_account_invoice_oca.template_voxel_invoice"

    def _get_product_discounts_data(self, line):
        discounts = []
        if line.discount:
            gross_amount = line.price_unit * line.quantity
            amount = line.currency_id.round(line.price_subtotal - gross_amount)
            discounts.append(
                {
                    "Qualifier": line.discount > 0.0 and "Descuento" or "Cargo",
                    "Type": line.discount > 0.0 and "Comercial" or "Otro",
                    "Rate": str(line.discount),
                    "Amount": str(amount),
                }
            )
        return discounts
