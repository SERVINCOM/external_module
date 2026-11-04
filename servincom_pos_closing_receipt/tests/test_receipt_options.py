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

    def test_receipt_fields_do_not_require_database_columns(self):
        fields_to_check = (
            ("pos.config", "servincom_hide_receipt_taxes"),
            ("pos.config", "servincom_anonymize_receipt_operator"),
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
