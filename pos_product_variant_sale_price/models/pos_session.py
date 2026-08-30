# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PosSession(models.Model):
    _inherit = "pos.session"

    @api.model
    def _get_variant_sale_price_domain(self):
        """Return a searchable equivalent of ``product.product.list_price``.

        ``product_variant_sale_price`` computes ``list_price`` from the stored
        variant ``fix_price`` or, when it is zero, from the stored template
        ``list_price``.  The computed field cannot be used in an ORM domain.
        """
        return [
            "|",
            ("fix_price", ">", 0),
            "&",
            ("fix_price", "=", 0),
            ("product_tmpl_id.list_price", ">=", 0),
        ]

    def _pos_has_valid_product(self):
        domain = [
            ("available_in_pos", "=", True),
            (
                "id",
                "not in",
                self.env["pos.config"]._get_special_products().ids,
            ),
            "|",
            ("active", "=", False),
            ("active", "=", True),
        ] + self._get_variant_sale_price_domain()
        return (
            self.env["product.product"]
            .sudo()
            .search_count(domain, limit=1)
            > 0
        )
