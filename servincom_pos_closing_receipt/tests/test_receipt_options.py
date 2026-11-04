# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestReceiptOptions(SavepointCase):
    def test_receipt_options_are_opt_in(self):
        config = self.env["pos.config"].new({})

        self.assertFalse(config.servincom_hide_receipt_taxes)
        self.assertFalse(config.servincom_anonymize_receipt_operator)

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
