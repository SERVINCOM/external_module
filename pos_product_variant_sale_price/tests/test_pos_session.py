# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPosSession(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env["product.product"].with_context(active_test=False)
        cls.PosSession = cls.env["pos.session"]

    @classmethod
    def _create_product(cls, name, template_price, fix_price=0):
        template = cls.env["product.template"].create(
            {
                "name": name,
                "list_price": template_price,
                "available_in_pos": True,
            }
        )
        product = template.product_variant_id
        product.fix_price = fix_price
        return product

    def test_stored_domain_matches_computed_list_price(self):
        products = self.Product.concat(
            self._create_product("Template positive", 100),
            self._create_product("Template negative", -100),
            self._create_product("Variant positive", -100, 50),
            self._create_product("Variant negative", 100, -50),
        )

        expected_ids = set(
            products.filtered(lambda product: product.list_price >= 0).ids
        )
        actual_ids = set(
            self.Product.search(
                [("id", "in", products.ids)]
                + self.PosSession._get_variant_sale_price_domain()
            ).ids
        )

        self.assertEqual(actual_ids, expected_ids)

    def test_pos_valid_product_check_accepts_nonstored_list_price(self):
        self._create_product("POS valid product", 100)

        self.assertTrue(self.PosSession._pos_has_valid_product())
