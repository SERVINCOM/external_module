# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestPosCustomerDisplay(TransactionCase):
    def test_pos_asset_bundle_compiles(self):
        self.env["ir.qweb"]._get_asset_nodes(
            "point_of_sale.assets",
            css=False,
            js=True,
            debug=False,
        )

    def test_customer_display_images_are_available_as_data_uris(self):
        image = (
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
            b"AAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        config = self.env["pos.config"].new(
            {
                "servincom_customer_display_background": image,
                "servincom_customer_display_sales_logo": image,
            }
        )

        config._compute_servincom_customer_display_background_uri()
        config._compute_servincom_customer_display_sales_logo_uri()

        self.assertTrue(
            config.servincom_customer_display_background_uri.startswith(
                "data:image/png;base64,"
            )
        )
        self.assertTrue(
            config.servincom_customer_display_sales_logo_uri.startswith(
                "data:image/png;base64,"
            )
        )
