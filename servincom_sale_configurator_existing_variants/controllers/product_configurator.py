from odoo.http import route

from odoo.addons.sale.controllers.product_configurator import (
    SaleProductConfiguratorController,
)


class ExistingVariantConfigurator(SaleProductConfiguratorController):
    # Republish the backend endpoints so Odoo dispatches through this extension.
    @route()
    def sale_product_configurator_get_values(self, *args, **kwargs):
        return super().sale_product_configurator_get_values(*args, **kwargs)

    @route()
    def sale_product_configurator_update_combination(self, *args, **kwargs):
        return super().sale_product_configurator_update_combination(*args, **kwargs)

    @route()
    def sale_product_configurator_get_optional_products(self, *args, **kwargs):
        return super().sale_product_configurator_get_optional_products(*args, **kwargs)

    def _get_product_information(self, product_template, *args, **kwargs):
        result = super()._get_product_information(product_template, *args, **kwargs)
        combinations = product_template._servincom_existing_configurator_combinations()
        if combinations is not None:
            result['servincom_combinations'] = combinations
        return result
