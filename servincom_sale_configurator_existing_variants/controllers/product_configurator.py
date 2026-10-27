from odoo.addons.sale.controllers.product_configurator import (
    SaleProductConfiguratorController,
)


class ExistingVariantConfigurator(SaleProductConfiguratorController):
    def _get_product_information(self, product_template, *args, **kwargs):
        result = super()._get_product_information(product_template, *args, **kwargs)
        combinations = product_template._servincom_existing_configurator_combinations()
        if combinations is not None:
            result['servincom_combinations'] = combinations
        return result
