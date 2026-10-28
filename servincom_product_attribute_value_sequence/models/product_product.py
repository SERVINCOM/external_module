# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    attribute_value_order_key = fields.Char(
        string="Attribute value order",
        compute="_compute_attribute_value_order_key",
        store=True,
    )

    @api.depends(
        "product_template_attribute_value_ids",
        "product_template_attribute_value_ids.attribute_line_id.sequence",
        "product_template_attribute_value_ids.attribute_id.sequence",
        "product_template_attribute_value_ids.product_attribute_value_id.sequence",
    )
    def _compute_attribute_value_order_key(self):
        for product in self:
            values = product.product_template_attribute_value_ids.sorted(
                key=lambda value: (
                    value.attribute_line_id.sequence,
                    value.attribute_id.sequence,
                    value.attribute_id.id,
                )
            )
            # Offset signed PostgreSQL integers so lexical and numeric orders agree.
            # IDs break equal-sequence ties exactly as product.attribute.value does.
            product.attribute_value_order_key = ":".join(
                f"{value.product_attribute_value_id.sequence + 2147483648:010d}"
                f"/{value.product_attribute_value_id.id:010d}"
                for value in values
            )
