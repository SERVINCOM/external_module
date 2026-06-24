# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._create_pos_customer_credit_lines()
        return orders

    def write(self, vals):
        result = super().write(vals)
        if "state" in vals and vals["state"] == "cancel":
            self._cancel_unpaid_credit_lines_from_cancelled_order()
        return result

    def _create_pos_customer_credit_lines(self):
        credit_model = self.env["pos.customer.credit.line"]
        for order in self:
            all_credit_payments = order.payment_ids.filtered(
                lambda payment: payment.payment_method_id.is_pos_customer_credit
            )
            credit_payments = all_credit_payments.filtered(lambda payment: payment.amount > 0.0)
            credit_refund_amount = abs(
                sum(all_credit_payments.filtered(lambda payment: payment.amount < 0.0).mapped("amount"))
            )
            if credit_refund_amount:
                order._apply_pos_credit_refund(credit_refund_amount)
            if not credit_payments:
                continue
            order._check_pos_credit_order_allowed()
            if credit_model.search_count([("pos_order_id", "=", order.id)]):
                existing_lines = credit_model.search(
                    [
                        ("pos_order_id", "=", order.id),
                        ("state", "!=", "cancelled"),
                    ]
                )
            else:
                existing_lines = credit_model.browse()
            credit_amount = sum(credit_payments.mapped("amount"))
            precision = order.currency_id.rounding
            if float_is_zero(credit_amount, precision_rounding=precision):
                continue
            if float_compare(credit_amount, 0.0, precision_rounding=precision) < 0:
                continue
            if existing_lines:
                if not any(existing_lines.mapped("amount_paid")):
                    line = existing_lines[:1]
                    line.amount_total = credit_amount
                    (existing_lines - line).action_cancel()
                    line._refresh_credit_state()
                continue
            credit_model.create(
                {
                    "partner_id": order.partner_id.id,
                    "pos_order_id": order.id,
                    "session_id": order.session_id.id,
                    "config_id": order.config_id.id,
                    "date_order": order.date_order,
                    "amount_total": credit_amount,
                    "currency_id": order.currency_id.id,
                    "company_id": order.company_id.id,
                    "note": _("Creado automáticamente desde el ticket %s")
                    % order.name,
                }
            )

    def _check_pos_credit_order_allowed(self):
        self.ensure_one()
        if not self.config_id.enable_pos_customer_credit:
            raise UserError(
                _(
                    "El punto de venta no tiene activada la gestión de "
                    "crédito de clientes."
                )
            )
        if not self.partner_id:
            raise UserError(_("Debe seleccionar un cliente para usar pago a crédito."))
        if not self.partner_id.pos_credit_customer:
            raise UserError(
                _("El cliente %s no está autorizado para crédito TPV.")
                % self.partner_id.display_name
            )

    def _apply_pos_credit_refund(self, refund_amount):
        self.ensure_one()
        self._check_pos_credit_order_allowed()
        pos_line_model = self.env["pos.order.line"]
        if "refunded_orderline_id" not in pos_line_model._fields:
            return
        source_orders = self.lines.mapped("refunded_orderline_id.order_id")
        source_credit_lines = self.env["pos.customer.credit.line"].search(
            [
                ("pos_order_id", "in", source_orders.ids),
                ("state", "in", ("open", "partial")),
            ],
            order="date_order asc, id asc",
        )
        remaining = refund_amount
        for credit_line in source_credit_lines:
            rounding = credit_line.currency_id.rounding
            if float_is_zero(remaining, precision_rounding=rounding):
                break
            if credit_line.amount_paid:
                credit_line.note = "%s\n%s" % (
                    credit_line.note or "",
                    _(
                        "La devolución %s no ajustó automáticamente esta deuda "
                        "porque ya tiene cobros aplicados."
                    )
                    % self.name,
                )
                continue
            applied = min(remaining, credit_line.amount_residual)
            credit_line.amount_total -= applied
            if float_is_zero(credit_line.amount_total, precision_rounding=rounding):
                credit_line.action_cancel()
            else:
                credit_line._refresh_credit_state()
            remaining -= applied

    def _cancel_unpaid_credit_lines_from_cancelled_order(self):
        for order in self:
            lines = self.env["pos.customer.credit.line"].search(
                [("pos_order_id", "=", order.id), ("state", "!=", "cancelled")]
            )
            for line in lines:
                if line.amount_paid:
                    raise ValidationError(
                        _(
                            "No se puede cancelar automáticamente la deuda %s "
                            "porque ya tiene cobros aplicados."
                        )
                        % line.display_name
                    )
                line.action_cancel()
