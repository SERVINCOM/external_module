from odoo import api, models
from odoo.http import request


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _servincom_existing_configurator_combinations(self):
        """None preserves native dynamic creation; [] means no valid existing choice."""
        self.ensure_one()
        if self.type == 'combo' or self.has_dynamic_attributes():
            return None
        variants = self.product_variant_ids.filtered('active')
        return [
            variant.product_template_attribute_value_ids.ids
            for variant in variants
            if self._is_combination_possible(
                variant.product_template_attribute_value_ids, ignore_no_variant=True
            )
        ]

    @api.model
    def _get_additional_configurator_data(
        self, product_or_template, date, currency, pricelist, **kwargs
    ):
        result = super()._get_additional_configurator_data(
            product_or_template, date, currency, pricelist, **kwargs
        )
        # Website and combo configurators share this hook but have different props.
        path = request.httprequest.path if request else ''
        if path not in {
            '/sale/product_configurator/get_values',
            '/sale/product_configurator/update_combination',
            '/sale/product_configurator/get_optional_products',
        }:
            return result
        template = (product_or_template.product_tmpl_id
                    if product_or_template._name == 'product.product'
                    else product_or_template)
        combinations = template._servincom_existing_configurator_combinations()
        if combinations is not None:
            result['servincom_combinations'] = combinations
        return result
