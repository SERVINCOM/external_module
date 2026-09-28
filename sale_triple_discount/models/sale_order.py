# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _recompute_prices(self):
        res = super()._recompute_prices()
        # Core resets discount and recomputes it explicitly. With triple
        # discounts, the pricelist discount must first be loaded into discount1.
        lines = self._get_update_prices_lines()
        lines._compute_discount1()
        lines._compute_discount()
        return res
