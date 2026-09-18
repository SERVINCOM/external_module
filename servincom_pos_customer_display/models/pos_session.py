# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _get_pos_ui_pos_config(self, params):
        config = super()._get_pos_ui_pos_config(params)
        # Data URIs are already present; avoid sending the same images twice.
        config.pop("servincom_customer_display_background", None)
        config.pop("servincom_customer_display_sales_logo", None)
        return config
