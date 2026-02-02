from odoo import models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    def _prepare_vals_for_pos(self, product):
        """
        Prepare warehouse info data to send a POS
        """
        self.ensure_one()
        product_with_warehouse = product.with_context(warehouse=self.id)
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "quantity": product_with_warehouse.immediately_usable_qty,
            "qty_on_hand": product_with_warehouse.qty_available,
            "product_id": product.id,
            "uom_id": product.uom_id.id,
        }
