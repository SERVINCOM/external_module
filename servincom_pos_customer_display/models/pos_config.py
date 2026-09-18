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
    servincom_customer_display_sales_logo = fields.Image(
        string="Sales panel logo",
        max_width=1024,
        max_height=512,
        help=(
            "Optional image displayed in the summary panel while a sale is active. "
            "Use a transparent image or include its final background in the image."
        ),
    )
    servincom_customer_display_sales_logo_uri = fields.Char(
        compute="_compute_servincom_customer_display_sales_logo_uri",
    )

    @api.depends("servincom_customer_display_background")
    def _compute_servincom_customer_display_background_uri(self):
        for config in self:
            config.servincom_customer_display_background_uri = (
                image_data_uri(config.servincom_customer_display_background)
                if config.servincom_customer_display_background
                else False
            )

    @api.depends("servincom_customer_display_sales_logo")
    def _compute_servincom_customer_display_sales_logo_uri(self):
        for config in self:
            config.servincom_customer_display_sales_logo_uri = (
                image_data_uri(config.servincom_customer_display_sales_logo)
                if config.servincom_customer_display_sales_logo
                else False
            )
