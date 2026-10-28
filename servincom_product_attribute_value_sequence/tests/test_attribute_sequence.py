# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAttributeSequence(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attribute = cls.env["product.attribute"].create(
            {
                "name": "Sequence test",
                "create_variant": "always",
                "value_ids": [
                    Command.create({"name": "First", "sequence": 10}),
                    Command.create({"name": "Second", "sequence": 20}),
                ],
            }
        )
        cls.first, cls.second = cls.attribute.value_ids
        cls.templates = cls.env["product.template"].create(
            [
                {
                    "name": name,
                    "attribute_line_ids": [
                        Command.create(
                            {
                                "attribute_id": cls.attribute.id,
                                "value_ids": [Command.set(cls.attribute.value_ids.ids)],
                            }
                        )
                    ],
                }
                for name in ["Sequence product A", "Sequence product B"]
            ]
        )

    def _values(self, template):
        return template.attribute_line_ids.product_template_value_ids

    def test_shared_sequence_and_no_variant_regeneration(self):
        variants = self.templates.product_variant_ids
        ids_before = set(variants.ids)
        variants.write({"default_code": "PRESERVE", "list_price": 42})
        selected = self._values(self.templates[0]).filtered(
            lambda value: value.product_attribute_value_id == self.second
        )
        selected.sequence = -10
        self.assertEqual(self.second.sequence, -10)
        for template in self.templates:
            self.assertEqual(
                self._values(template)._only_active().product_attribute_value_id.ids,
                [self.second.id, self.first.id],
            )
        self.assertEqual(set(self.templates.product_variant_ids.ids), ids_before)
        self.assertEqual(set(variants.mapped("default_code")), {"PRESERVE"})
        self.assertEqual(set(variants.mapped("list_price")), {42})

    def test_native_value_edit_updates_both_products(self):
        self.second.sequence = 0
        for template in self.templates:
            self.assertEqual(
                self._values(template)[0].product_attribute_value_id, self.second
            )
            self.assertEqual(self._values(template)[0].sequence, 0)

    def test_variant_order_and_equal_sequences(self):
        self.second.sequence = -1
        variants = self.env["product.product"].search(
            [("product_tmpl_id", "=", self.templates[0].id)],
            order="attribute_value_order_key, id",
        )
        self.assertEqual(
            variants[0].product_template_attribute_value_ids.product_attribute_value_id,
            self.second,
        )
        self.second.sequence = self.first.sequence
        variants = variants.sorted("attribute_value_order_key")
        self.assertEqual(
            variants[0].product_template_attribute_value_ids.product_attribute_value_id,
            self.first,
        )

    def test_multiple_attributes_and_line_order(self):
        other = self.env["product.attribute"].create(
            {
                "name": "Other sequence test",
                "create_variant": "always",
                "value_ids": [
                    Command.create({"name": "Small", "sequence": 10}),
                    Command.create({"name": "Large", "sequence": 20}),
                ],
            }
        )
        template = self.templates[0]
        template.attribute_line_ids.sequence = 10
        template.write(
            {
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": other.id,
                            "sequence": 20,
                            "value_ids": [Command.set(other.value_ids.ids)],
                        }
                    )
                ]
            }
        )

        def combinations():
            variants = template.product_variant_ids.sorted("attribute_value_order_key")
            return [
                tuple(
                    variant.product_template_attribute_value_ids.filtered(
                        lambda value: value.attribute_id == attribute
                    ).product_attribute_value_id.id
                    for attribute in (self.attribute, other)
                )
                for variant in variants
            ]

        small, large = other.value_ids
        self.assertEqual(
            combinations(),
            [
                (self.first.id, small.id),
                (self.first.id, large.id),
                (self.second.id, small.id),
                (self.second.id, large.id),
            ],
        )
        template.attribute_line_ids.filtered(
            lambda line: line.attribute_id == other
        ).sequence = 0
        self.assertEqual(
            combinations(),
            [
                (self.first.id, small.id),
                (self.second.id, small.id),
                (self.first.id, large.id),
                (self.second.id, large.id),
            ],
        )

    def test_action_scoped_to_product(self):
        template = self.templates[0]
        action = template.action_open_ordered_variants()
        self.assertEqual(action["domain"], [("product_tmpl_id", "=", template.id)])
        self.assertEqual(action["context"]["default_product_tmpl_id"], template.id)
        self.assertEqual(
            action["views"][0],
            (
                self.env.ref(
                    "servincom_product_attribute_value_sequence.product_variant_ordered_list"
                ).id,
                "list",
            ),
        )
