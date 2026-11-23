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

    def _servincom_descriptive_sale_lines(self):
        self.ensure_one()
        # Fail open for commercial choices. Hiding these would lose user input
        # or change a price; keep the native configurator in those cases.
        lines = self.attribute_line_ids.filtered(
            lambda line: line.attribute_id.sale_descriptive
            and line.attribute_id.create_variant == 'no_variant'
            and not any(v.is_custom or v.price_extra for v in line.product_template_value_ids)
        )
        values = lines.product_template_value_ids
        if values:
            exclusions = self.env['product.template.attribute.exclusion'].search([
                '|', ('product_template_attribute_value_id', 'in', values.ids),
                ('value_ids', 'in', values.ids),
            ])
            excluded = (exclusions.product_template_attribute_value_id | exclusions.value_ids)
            lines = lines.filtered(lambda line: not (line.product_template_value_ids & excluded))
        return lines

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
        result['servincom_descriptive_line_ids'] = (
            template._servincom_descriptive_sale_lines().ids
        )
        combinations = template._servincom_existing_configurator_combinations()
        if combinations is not None:
            result['servincom_combinations'] = combinations
        return result
