from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    sale_descriptive = fields.Boolean(
        string='Descriptive in sales',
        help='Keep this attribute as product information, without a choice in the '
             'sales configurator. Only non-variant attributes without custom '
             'values, surcharges or exclusions can be omitted.',
    )

    @api.constrains('sale_descriptive', 'create_variant')
    def _check_sale_descriptive(self):
        if any(a.sale_descriptive and a.create_variant != 'no_variant' for a in self):
            raise ValidationError(_('Descriptive sales attributes must not create variants.'))
