# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from pathlib import Path

from lxml import etree

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductCardTemplate(TransactionCase):
    def test_product_card_image_uses_native_lazy_loading(self):
        template_path = (
            Path(__file__).resolve().parents[1]
            / "static"
            / "src"
            / "xml"
            / "product_card.xml"
        )
        template = etree.parse(str(template_path))
        inheritance_nodes = template.xpath(
            "//t[@t-inherit='point_of_sale.ProductCard']"
            "/xpath[@expr=\"//div[hasclass('product-img')]/img\"]"
        )

        self.assertEqual(len(inheritance_nodes), 1)
        attributes = {
            attribute.get("name"): (attribute.text or "").strip()
            for attribute in inheritance_nodes[0].xpath("./attribute")
        }
        self.assertEqual(attributes.get("loading"), "lazy")
        self.assertEqual(attributes.get("decoding"), "async")
