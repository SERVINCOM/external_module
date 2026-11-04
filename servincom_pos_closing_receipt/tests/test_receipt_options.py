# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.modules.module import get_module_resource
from odoo.tests.common import SavepointCase


class TestReceiptOptions(SavepointCase):
    def test_receipt_options_are_opt_in(self):
        config = self.env["pos.config"].new({})

        self.assertFalse(config.servincom_hide_receipt_taxes)
        self.assertFalse(config.servincom_anonymize_receipt_operator)
        self.assertFalse(config.servincom_customize_receipt_operator)
        self.assertEqual(config.servincom_receipt_operator_display, "name")

    def test_receipt_fields_do_not_require_database_columns(self):
        fields_to_check = (
            ("pos.config", "servincom_hide_receipt_taxes"),
            ("pos.config", "servincom_anonymize_receipt_operator"),
            ("pos.config", "servincom_customize_receipt_operator"),
            ("pos.config", "servincom_receipt_operator_display"),
            ("res.users", "servincom_pos_receipt_operator_label"),
            ("hr.employee", "servincom_pos_receipt_operator_label"),
        )

        for model_name, field_name in fields_to_check:
            self.assertFalse(self.env[model_name]._fields[field_name].store)

    def test_operator_identifier_is_loaded_for_users_and_employees(self):
        session_model = self.env["pos.session"]

        user_fields = session_model._loader_params_res_users()["search_params"][
            "fields"
        ]
        employee_fields = session_model._loader_params_hr_employee()[
            "search_params"
        ]["fields"]

        self.assertIn("servincom_pos_receipt_operator_label", user_fields)
        self.assertIn("servincom_pos_receipt_operator_label", employee_fields)

    def test_receipt_template_inherits_namespaced_odoo_template(self):
        template_path = get_module_resource(
            "servincom_pos_closing_receipt",
            "static",
            "src",
            "xml",
            "order_receipt_templates.xml",
        )
        template = etree.parse(template_path).xpath(
            "//t[@t-name='servincom_pos_closing_receipt.OrderReceiptOptions']"
        )[0]

        self.assertEqual(template.get("t-inherit"), "point_of_sale.OrderReceipt")

    def test_receipt_operator_display_has_expected_choices(self):
        selection = dict(
            self.env["pos.config"]
            ._fields["servincom_receipt_operator_display"]
            .selection
        )

        self.assertEqual(set(selection), {"name", "identifier", "hidden"})

    def test_operator_display_settings_are_opt_in(self):
        view_path = get_module_resource(
            "servincom_pos_closing_receipt",
            "views",
            "res_config_settings_views.xml",
        )
        view = etree.parse(view_path)

        self.assertTrue(
            view.xpath(
                "//field[@name='pos_servincom_customize_receipt_operator']"
            )
        )
        option_group = view.xpath(
            "//div[field[@name='pos_servincom_receipt_operator_display']]"
        )[0]
        self.assertIn(
            "pos_servincom_customize_receipt_operator",
            option_group.get("attrs", ""),
        )
        operator_field = option_group.xpath(
            ".//field[@name='pos_servincom_receipt_operator_display']"
        )[0]
        self.assertNotIn("horizontal", operator_field.get("options", ""))
