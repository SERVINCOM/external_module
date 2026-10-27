from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestExistingCombinations(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        attributes = cls.env['product.attribute'].create([
            {'name': 'Piece', 'create_variant': 'always',
             'value_ids': [Command.create({'name': name}) for name in ('A', 'B')]},
            {'name': 'Size', 'create_variant': 'always',
             'value_ids': [Command.create({'name': name}) for name in ('10', '20', '30')]},
        ])
        cls.template = cls.env['product.template'].create({
            'name': 'Configurator fixture',
            'attribute_line_ids': [Command.create({
                'attribute_id': a.id, 'value_ids': [Command.set(a.value_ids.ids)],
            }) for a in attributes],
        })

    def test_deleted_and_archived_variants_are_not_returned(self):
        variants = self.template.product_variant_ids.sorted('id')
        removed = variants[:1]
        archived = variants[1:3]
        expected = variants[3:]
        removed.unlink()
        archived.action_archive()
        actual = self.template._servincom_existing_configurator_combinations()
        self.assertEqual(
            {frozenset(row) for row in actual},
            {frozenset(v.product_template_attribute_value_ids.ids) for v in expected},
        )
        self.assertEqual(len(actual), 3)

    def test_no_stock_requirement(self):
        # All fixtures have zero stock; inventory is deliberately not a filter.
        self.assertEqual(len(self.template._servincom_existing_configurator_combinations()), 6)

    def test_dynamic_products_keep_native_behavior(self):
        attribute = self.env['product.attribute'].create({
            'name': 'Dynamic size', 'create_variant': 'dynamic',
            'value_ids': [Command.create({'name': name}) for name in ('Small', 'Large')],
        })
        template = self.env['product.template'].create({
            'name': 'Dynamic fixture',
            'attribute_line_ids': [Command.create({
                'attribute_id': attribute.id,
                'value_ids': [Command.set(attribute.value_ids.ids)],
            })],
        })
        self.assertIsNone(template._servincom_existing_configurator_combinations())

    def test_empty_active_variants(self):
        self.template.product_variant_ids.action_archive()
        self.assertEqual(self.template._servincom_existing_configurator_combinations(), [])
