# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


def _empty_payment_breakdown():
    return {
        "sales_amount": 0.0,
        "refund_amount": 0.0,
        "refunds": [],
        "credit_amount": 0.0,
        "credit_payments": [],
    }


def _get_payment_method_row(closing_data, payment_method_id, payment_totals):
    cash_details = closing_data.get("default_cash_details") or {}
    if cash_details.get("id") == payment_method_id:
        return cash_details, True

    method_rows = {
        method_data["id"]: method_data
        for method_data in closing_data.get("other_payment_methods", [])
    }
    method_data = method_rows.get(payment_method_id)
    if method_data:
        return method_data, False

    method_data = {
        "name": payment_totals["name"],
        "amount": 0.0,
        "number": 0,
        "id": payment_method_id,
        "type": payment_totals["type"],
    }
    closing_data.setdefault("other_payment_methods", []).append(method_data)
    return method_data, False


def _merge_credit_payment_totals(
    closing_data, payment_totals, pos_payment_totals=None
):
    """Add debt settlements and an informational payment breakdown."""
    for payment_method_id, totals in (pos_payment_totals or {}).items():
        method_data, _is_cash = _get_payment_method_row(
            closing_data, payment_method_id, totals
        )
        breakdown = method_data.setdefault(
            "servincom_breakdown", _empty_payment_breakdown()
        )
        breakdown["sales_amount"] += totals.get("sales_amount", 0.0)
        breakdown["refund_amount"] += totals.get("refund_amount", 0.0)
        breakdown["refunds"].extend(totals.get("refunds", []))

    for payment_method_id, totals in payment_totals.items():
        method_data, is_cash = _get_payment_method_row(
            closing_data, payment_method_id, totals
        )
        breakdown = method_data.setdefault(
            "servincom_breakdown", _empty_payment_breakdown()
        )
        breakdown["credit_amount"] += totals["amount"]
        breakdown["credit_payments"].extend(totals.get("payments", []))
        if not is_cash:
            method_data["amount"] = method_data.get("amount", 0.0) + totals["amount"]
            method_data["number"] = method_data.get("number", 0) + totals["number"]
    return closing_data


class PosSession(models.Model):
    _inherit = "pos.session"

    pos_credit_payment_ids = fields.One2many(
        comodel_name="pos.customer.credit.payment",
        inverse_name="session_id",
        string="Cobros deuda clientes",
    )
    pos_credit_payment_total = fields.Monetary(
        string="Total cobros deuda clientes",
        compute="_compute_pos_credit_payments",
        currency_field="currency_id",
    )
    pos_credit_payment_count = fields.Integer(
        string="Número de cobros deuda clientes",
        compute="_compute_pos_credit_payments",
    )

    def _compute_pos_credit_payments(self):
        for session in self:
            payments = session.pos_credit_payment_ids.filtered(
                lambda payment: payment.state == "posted"
            )
            session.pos_credit_payment_total = sum(payments.mapped("amount"))
            session.pos_credit_payment_count = len(payments)

    def action_view_pos_credit_payments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "servincom_pos_customer_credit_settlement.action_pos_customer_credit_payment"
        )
        action["domain"] = [("session_id", "=", self.id)]
        action["context"] = {"default_session_id": self.id}
        return action

    def _get_pos_credit_closing_totals(self):
        self.ensure_one()
        payments = self.sudo().pos_credit_payment_ids.filtered(
            lambda payment: payment.state == "posted"
        )
        totals = {}
        for payment in payments.sorted("id"):
            payment_method = payment.payment_method_id
            method_totals = totals.setdefault(
                payment_method.id,
                {
                    "name": payment_method.name,
                    "type": payment_method.type,
                    "amount": 0.0,
                    "number": 0,
                    "payments": [],
                },
            )
            method_totals["amount"] += payment.amount
            method_totals["number"] += 1
            method_totals["payments"].append(
                {
                    "name": payment.name,
                    "partner_name": payment.partner_id.display_name,
                    "amount": payment.amount,
                }
            )
        return totals

    def _get_pos_order_payment_closing_totals(self):
        self.ensure_one()
        orders = self.order_ids.filtered(
            lambda order: order.state in ("paid", "invoiced")
        )
        payments = orders.payment_ids.filtered(
            lambda payment: payment.payment_method_id.type != "pay_later"
        )
        totals = {}
        for payment in payments.sorted("id"):
            payment_method = payment.payment_method_id
            method_totals = totals.setdefault(
                payment_method.id,
                {
                    "name": payment_method.name,
                    "type": payment_method.type,
                    "sales_amount": 0.0,
                    "refund_amount": 0.0,
                    "refunds": [],
                },
            )
            is_refund = (
                payment.amount < 0.0
                and not payment.is_change
                and payment.pos_order_id.amount_total < 0.0
            )
            if not is_refund:
                method_totals["sales_amount"] += payment.amount
                continue
            method_totals["refund_amount"] += payment.amount
            method_totals["refunds"].append(
                {
                    "name": payment.pos_order_id.name,
                    "amount": payment.amount,
                }
            )
        return totals

    def get_closing_control_data(self):
        closing_data = super().get_closing_control_data()
        return _merge_credit_payment_totals(
            closing_data,
            self._get_pos_credit_closing_totals(),
            self._get_pos_order_payment_closing_totals(),
        )
