# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosSession(models.Model):
    _inherit = "pos.session"

    def get_servincom_closing_receipt_data(
        self, closing_note=False, payment_states=None
    ):
        self.ensure_one()
        closing_data = self.get_closing_control_data()
        payment_states = payment_states or {}

        default_cash_details = closing_data.get("default_cash_details") or {}
        cash_payment_method_id = default_cash_details.get("id")
        cash_state = self._servincom_get_payment_state(
            payment_states, cash_payment_method_id
        )
        cash_expected = default_cash_details.get("amount", 0.0)
        cash_counted = cash_state.get("counted")
        cash_difference = self._servincom_get_difference(
            cash_state, cash_counted, cash_expected
        )
        cash_moves = default_cash_details.get("moves") or []
        cash_in_total = sum(
            move.get("amount", 0.0) for move in cash_moves if move.get("amount", 0.0) > 0
        )
        cash_out_total = sum(
            move.get("amount", 0.0) for move in cash_moves if move.get("amount", 0.0) < 0
        )

        now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        return {
            "company_name": self.company_id.name,
            "pos_name": self.config_id.display_name,
            "session_name": self.name,
            "cashier_name": self.env.user.name or self.user_id.name,
            "date_time": now.strftime("%d/%m/%Y %H:%M:%S"),
            "orders_count": closing_data["orders_details"]["quantity"],
            "orders_total": closing_data["orders_details"]["amount"],
            "opening_note": closing_data.get("opening_notes") or "",
            "closing_note": closing_note or "",
            "cash": {
                "name": default_cash_details.get("name") or "",
                "expected": cash_expected,
                "counted": cash_counted,
                "difference": cash_difference,
                "opening": default_cash_details.get("opening", 0.0),
                "cash_in_total": cash_in_total,
                "cash_out_total": cash_out_total,
                "payment_amount": default_cash_details.get("payment_amount", 0.0),
                "moves": cash_moves,
            },
            "payment_methods": self._servincom_get_closing_payment_methods(
                closing_data, payment_states
            ),
        }

    def _servincom_get_closing_payment_methods(self, closing_data, payment_states):
        self.ensure_one()
        payment_methods = []
        default_cash_details = closing_data.get("default_cash_details")
        if default_cash_details:
            cash_state = self._servincom_get_payment_state(
                payment_states, default_cash_details["id"]
            )
            expected = default_cash_details.get("amount", 0.0)
            counted = cash_state.get("counted")
            payment_methods.append(
                {
                    "name": default_cash_details["name"],
                    "category": "Efectivo",
                    "expected": expected,
                    "counted": counted,
                    "difference": self._servincom_get_difference(
                        cash_state, counted, expected
                    ),
                    "show_counted": True,
                }
            )

        for payment_method in closing_data.get("other_payment_methods", []):
            payment_state = self._servincom_get_payment_state(
                payment_states, payment_method["id"]
            )
            expected = payment_method.get("amount", 0.0)
            counted = payment_state.get("counted")
            payment_methods.append(
                {
                    "name": payment_method["name"],
                    "category": self._servincom_get_payment_category(
                        payment_method.get("type")
                    ),
                    "expected": expected,
                    "counted": counted,
                    "difference": self._servincom_get_difference(
                        payment_state, counted, expected
                    ),
                    "show_counted": counted is not None,
                }
            )
        return payment_methods

    def _servincom_get_payment_state(self, payment_states, payment_method_id):
        if not payment_method_id:
            return {}
        return (
            payment_states.get(str(payment_method_id))
            or payment_states.get(payment_method_id)
            or {}
        )

    def _servincom_get_difference(self, payment_state, counted, expected):
        if "difference" in payment_state and payment_state["difference"] is not None:
            return payment_state["difference"]
        if counted is None:
            return None
        return self.currency_id.round(counted - expected)

    def _servincom_get_payment_category(self, payment_method_type):
        if payment_method_type == "bank":
            return "Banco"
        if payment_method_type == "pay_later":
            return "A cuenta de cliente"
        return "Otros métodos de pago"
