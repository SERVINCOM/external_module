# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_servincom_customer_display_background = fields.Image(
        related="pos_config_id.servincom_customer_display_background",
        readonly=False,
    )
    pos_servincom_customer_display_message = fields.Char(
        related="pos_config_id.servincom_customer_display_message",
        readonly=False,
    )
    pos_servincom_customer_display_show_logo = fields.Boolean(
        related="pos_config_id.servincom_customer_display_show_logo",
        readonly=False,
    )
