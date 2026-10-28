# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.tools import SQL


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
        values = self.product_template_attribute_value_ids.product_attribute_value_id
        # ORM integer domains conflate NULL and zero. Preserve PostgreSQL's
        # native NULLS LAST ordering without rewriting legacy attribute values.
        unset_sequences = {
            value_id
            for (value_id,) in self.env.execute_query(
                SQL(
                    "SELECT id FROM product_attribute_value "
                    "WHERE id IN %s AND sequence IS NULL",
                    tuple(values.ids) or (0,),
                    to_flush=values._fields["sequence"],
                )
            )
        }
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
                f"{int(value.product_attribute_value_id.id in unset_sequences)}"
                f"{value.product_attribute_value_id.sequence + 2147483648:010d}"
                f"/{value.product_attribute_value_id.id:010d}"
                for value in values
            )
