from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestDescriptive(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attribute = cls.env['product.attribute'].create({
            'name': 'Compatibility', 'create_variant': 'no_variant',
            'sale_descriptive': True,
            'value_ids': [Command.create({'name': 'Freezer'}),
                          Command.create({'name': 'Dishwasher'})],
        })
        cls.product = cls.env['product.template'].create({
            'name': 'Container',
            'attribute_line_ids': [Command.create({
                'attribute_id': cls.attribute.id,
                'value_ids': [Command.set(cls.attribute.value_ids.ids)],
            })],
        })

    def test_only_explicit_descriptive_lines(self):
        self.assertEqual(self.product._servincom_descriptive_sale_lines(),
                         self.product.attribute_line_ids)
        self.attribute.sale_descriptive = False
        self.assertFalse(self.product._servincom_descriptive_sale_lines())

    def test_variant_attribute_rejected(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env['product.attribute'].create({
                'name': 'Size', 'create_variant': 'always', 'sale_descriptive': True,
            })

    def test_priced_choice_is_preserved(self):
        self.product.attribute_line_ids.product_template_value_ids[0].price_extra = 5
        self.assertFalse(self.product._servincom_descriptive_sale_lines())

    def test_custom_choice_is_preserved(self):
        self.attribute.value_ids[0].is_custom = True
        self.assertFalse(self.product._servincom_descriptive_sale_lines())

    def test_exclusions_are_preserved(self):
        values = self.product.attribute_line_ids.product_template_value_ids
        self.env['product.template.attribute.exclusion'].create({
            'product_template_attribute_value_id': values[0].id,
            'product_tmpl_id': self.product.id,
            'value_ids': [Command.set(values[1].ids)],
        })
        self.assertFalse(self.product._servincom_descriptive_sale_lines())
