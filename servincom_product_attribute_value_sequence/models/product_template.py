# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_open_ordered_variants(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "product.product_variant_action"
        )
        view = self.env.ref(
            "servincom_product_attribute_value_sequence.product_variant_ordered_list"
        )
        action["views"] = [
            (view.id if mode == "list" else view_id, mode)
            for view_id, mode in action["views"]
        ]
        action["context"] = dict(
            self.env.context,
            search_default_product_tmpl_id=[self.id],
            default_product_tmpl_id=self.id,
            create=False,
        )
        action["domain"] = [("product_tmpl_id", "=", self.id)]
        return action
