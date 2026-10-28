# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    sequence = fields.Integer(
        related="product_attribute_value_id.sequence",
        readonly=False,
        store=True,
        string="Global sequence",
        help=(
            "Changing this order affects every product using the same attribute value."
        ),
    )
