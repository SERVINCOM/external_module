# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from ast import literal_eval
from pathlib import Path

from lxml import etree

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductCardTemplate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module_path = Path(__file__).resolve().parents[1]
        cls.template = etree.parse(
            str(cls.module_path / "static" / "src" / "xml" / "product_card.xml")
        )

    @staticmethod
    def _attributes(inheritance_node):
        return {
            attribute.get("name"): (attribute.text or "").strip()
            for attribute in inheritance_node.xpath("./attribute")
        }

    def test_product_card_image_container_is_observed(self):
        inheritance_nodes = self.template.xpath(
            "//t[@t-inherit='point_of_sale.ProductCard']"
            "/xpath[@expr=\"//div[hasclass('product-img')]\"]"
        )

        self.assertEqual(len(inheritance_nodes), 1)
        self.assertEqual(
            self._attributes(inheritance_nodes[0]).get("t-ref"),
            "deferredImageContainer",
        )

    def test_product_card_image_is_deferred(self):
        inheritance_nodes = self.template.xpath(
            "//t[@t-inherit='point_of_sale.ProductCard']"
            "/xpath[@expr=\"//div[hasclass('product-img')]/img\"]"
        )

        self.assertEqual(len(inheritance_nodes), 1)
        attributes = self._attributes(inheritance_nodes[0])
        self.assertEqual(attributes.get("t-if"), "deferredImageState.src")
        self.assertEqual(attributes.get("t-att-src"), "deferredImageState.src")
        self.assertEqual(attributes.get("t-on-load"), "onDeferredImageSettled")
        self.assertEqual(attributes.get("t-on-error"), "onDeferredImageSettled")
        self.assertEqual(attributes.get("loading"), "lazy")
        self.assertEqual(attributes.get("decoding"), "async")

    def test_pos_assets_include_image_queue(self):
        manifest = literal_eval((self.module_path / "__manifest__.py").read_text())
        assets = manifest["assets"]["point_of_sale._assets_pos"]

        self.assertIn(
            "pos_product_image_lazy_load/static/src/app/"
            "product_card_image_queue.js",
            assets,
        )
