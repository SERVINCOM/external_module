# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ReportVoxelInvoice(models.AbstractModel):
    _inherit = "report.edi_voxel_account_invoice_oca.template_voxel_invoice"

    def _is_voxel_exportable_product_line(self, line):
        if line.display_type in ("line_section", "line_note"):
            return False
        if line.display_type and line.display_type != "product":
            return False
        if not line.product_id and line.currency_id.is_zero(line.price_subtotal):
            return False
        return True

    def _get_products_data(self, invoice):
        return [
            {
                "product": self._get_product_data(line),
                "taxes": self._get_product_taxes_data(line),
                "discounts": self._get_product_discounts_data(line),
            }
            for line in invoice.invoice_line_ids.filtered(
                self._is_voxel_exportable_product_line
            )
        ]

    def _get_product_data(self, line):
        product = super()._get_product_data(line)
        fallback_name = line.name or line.product_id.display_name or str(line.id)
        product["SupplierSKU"] = product.get("SupplierSKU") or fallback_name
        product["Item"] = product.get("Item") or fallback_name
        product["Total"] = str(line.currency_id.round(line.price_unit * line.quantity))
        return product

    def _get_product_discounts_data(self, line):
        discounts = []
        if line.discount:
            gross_amount = line.price_unit * line.quantity
            amount = abs(line.currency_id.round(line.price_subtotal - gross_amount))
            discounts.append(
                {
                    "Qualifier": line.discount > 0.0 and "Descuento" or "Cargo",
                    "Type": line.discount > 0.0 and "Comercial" or "Otro",
                    "Rate": str(abs(line.discount)),
                    "Amount": str(amount),
                }
            )
        return discounts

    def _get_product_taxes_data(self, line):
        taxes = []
        price_unit = line.quantity and line.price_subtotal / line.quantity or 0.0
        tax_values = line.tax_ids.compute_all(
            price_unit,
            line.currency_id,
            line.quantity,
            product=line.product_id,
            partner=line.move_id.partner_id,
            is_refund=line.move_id.move_type in ("out_refund", "in_refund"),
        )
        for tax_data in tax_values.get("taxes", []):
            tax = self.env["account.tax"].browse(tax_data["id"])
            rate = tax.amount_type != "group" and str(tax.amount) or False
            taxes.append(
                {
                    "Type": tax.voxel_tax_code,
                    "Rate": rate,
                    "Base": str(line.currency_id.round(tax_data["base"])),
                    "Amount": str(abs(line.currency_id.round(tax_data["amount"]))),
                }
            )
        return taxes
