from odoo import models


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
