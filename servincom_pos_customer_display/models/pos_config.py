# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import image_data_uri


class PosConfig(models.Model):
    _inherit = "pos.config"

    servincom_customer_display_background = fields.Image(
        string="Customer display background",
        max_width=1920,
        max_height=1080,
        help="Optional background image for the customer-facing POS display.",
    )
    servincom_customer_display_background_uri = fields.Char(
        compute="_compute_servincom_customer_display_background_uri",
    )
    servincom_customer_display_message = fields.Char(
        string="Customer display message",
        translate=True,
        help="Message displayed next to the company logo on the customer screen.",
    )
    servincom_customer_display_show_logo = fields.Boolean(
        string="Show company logo over the background",
        default=True,
        help="Disable this option when the custom background already includes the logo.",
    )

    @api.depends("servincom_customer_display_background")
    def _compute_servincom_customer_display_background_uri(self):
        for config in self:
            config.servincom_customer_display_background_uri = (
                image_data_uri(config.servincom_customer_display_background)
                if config.servincom_customer_display_background
                else False
            )
