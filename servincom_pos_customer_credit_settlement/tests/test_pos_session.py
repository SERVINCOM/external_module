# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from ..models.pos_session import _merge_credit_payment_totals


class TestPosSessionClosingData(TransactionCase):
    def test_credit_card_settlement_is_added_to_existing_method(self):
        closing_data = {
            "payments_amount": 20.0,
            "other_payment_methods": [
                {
                    "name": "Datáfono C7",
                    "amount": 5.0,
                    "number": 1,
                    "id": 7,
                    "type": "bank",
                }
            ],
        }

        result = _merge_credit_payment_totals(
            closing_data,
            {
                7: {
                    "name": "Datáfono C7",
                    "type": "bank",
                    "amount": 15.84,
                    "number": 1,
                }
            },
        )

        self.assertAlmostEqual(result["other_payment_methods"][0]["amount"], 20.84)
        self.assertEqual(result["other_payment_methods"][0]["number"], 2)
        self.assertEqual(result["payments_amount"], 20.0)

    def test_credit_card_settlement_adds_missing_method_row(self):
        closing_data = {"other_payment_methods": []}

        result = _merge_credit_payment_totals(
            closing_data,
            {
                9: {
                    "name": "Datáfono adicional",
                    "type": "bank",
                    "amount": 12.5,
                    "number": 1,
                }
            },
        )

        self.assertEqual(
            result["other_payment_methods"],
            [
                {
                    "name": "Datáfono adicional",
                    "amount": 12.5,
                    "number": 1,
                    "id": 9,
                    "type": "bank",
                }
            ],
        )
