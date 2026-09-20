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
                    "payments": [
                        {
                            "name": "PCCP/2026/00001",
                            "partner_name": "Cliente prueba",
                            "amount": 15.84,
                        }
                    ],
                }
            },
            {
                7: {
                    "name": "Datáfono C7",
                    "type": "bank",
                    "sales_amount": 7.30,
                    "refund_amount": -2.30,
                    "refunds": [
                        {"name": "Pedido TEST-0001", "amount": -2.30}
                    ],
                }
            },
        )

        self.assertAlmostEqual(result["other_payment_methods"][0]["amount"], 20.84)
        self.assertEqual(result["other_payment_methods"][0]["number"], 2)
        self.assertEqual(result["payments_amount"], 20.0)
        self.assertEqual(
            result["other_payment_methods"][0]["servincom_breakdown"],
            {
                "sales_amount": 7.30,
                "refund_amount": -2.30,
                "refunds": [
                    {"name": "Pedido TEST-0001", "amount": -2.30}
                ],
                "credit_amount": 15.84,
                "credit_payments": [
                    {
                        "name": "PCCP/2026/00001",
                        "partner_name": "Cliente prueba",
                        "amount": 15.84,
                    }
                ],
            },
        )
        breakdown = result["other_payment_methods"][0]["servincom_breakdown"]
        self.assertAlmostEqual(
            result["other_payment_methods"][0]["amount"],
            breakdown["sales_amount"]
            + breakdown["refund_amount"]
            + breakdown["credit_amount"],
        )

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
                    "payments": [],
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
                    "servincom_breakdown": {
                        "sales_amount": 0.0,
                        "refund_amount": 0.0,
                        "refunds": [],
                        "credit_amount": 12.5,
                        "credit_payments": [],
                    },
                }
            ],
        )

    def test_cash_settlement_is_only_added_to_breakdown(self):
        closing_data = {
            "default_cash_details": {
                "name": "Efectivo",
                "amount": 24.65,
                "number": 1,
                "id": 1,
                "type": "cash",
            },
            "other_payment_methods": [],
        }

        result = _merge_credit_payment_totals(
            closing_data,
            {
                1: {
                    "name": "Efectivo",
                    "type": "cash",
                    "amount": 4.65,
                    "number": 1,
                    "payments": [
                        {
                            "name": "PCCP/2026/00002",
                            "partner_name": "Cliente prueba",
                            "amount": 4.65,
                        }
                    ],
                }
            },
            {
                1: {
                    "name": "Efectivo",
                    "type": "cash",
                    "sales_amount": 20.0,
                    "refund_amount": 0.0,
                    "refunds": [],
                }
            },
        )

        self.assertAlmostEqual(result["default_cash_details"]["amount"], 24.65)
        self.assertEqual(
            result["default_cash_details"]["servincom_breakdown"][
                "credit_amount"
            ],
            4.65,
        )
        breakdown = result["default_cash_details"]["servincom_breakdown"]
        self.assertAlmostEqual(
            result["default_cash_details"]["amount"],
            breakdown["sales_amount"]
            + breakdown["refund_amount"]
            + breakdown["credit_amount"],
        )
        self.assertEqual(result["other_payment_methods"], [])
