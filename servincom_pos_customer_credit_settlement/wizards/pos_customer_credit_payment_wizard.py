# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class PosCustomerCreditPaymentWizard(models.TransientModel):
    _name = "pos.customer.credit.payment.wizard"
    _description = "POS Customer Credit Payment Wizard"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Cliente",
        required=True,
        domain=[("pos_credit_customer", "=", True)],
    )
    line_ids = fields.Many2many(
        comodel_name="pos.customer.credit.line",
        string="Tickets pendientes",
        domain="[('partner_id', '=', partner_id), ('state', 'in', ('open', 'partial'))]",
    )
    session_id = fields.Many2one(
        comodel_name="pos.session",
        string="Sesión TPV",
        required=True,
        domain=[("state", "in", ("opening_control", "opened"))],
    )
    available_payment_method_ids = fields.Many2many(
        comodel_name="pos.payment.method",
        compute="_compute_available_payment_method_ids",
    )
    payment_method_id = fields.Many2one(
        comodel_name="pos.payment.method",
        string="Método de cobro",
        required=True,
        domain="[('id', 'in', available_payment_method_ids)]",
    )
    amount = fields.Monetary(string="Importe a cobrar", required=True)
    amount_selected = fields.Monetary(
        string="Pendiente seleccionado",
        compute="_compute_amount_selected",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moneda",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids") or []
        if active_model == "pos.customer.credit.line" and active_ids:
            lines = self.env["pos.customer.credit.line"].browse(active_ids).filtered(
                lambda line: line.state in ("open", "partial")
            )
            if lines:
                partners = lines.mapped("partner_id")
                currencies = lines.mapped("currency_id")
                companies = lines.mapped("company_id")
                if len(partners) > 1:
                    raise UserError(_("Seleccione tickets de un único cliente."))
                if len(currencies) > 1:
                    raise UserError(_("Seleccione tickets de una única moneda."))
                if len(companies) > 1:
                    raise UserError(_("Seleccione tickets de una única compañía."))
                values.update(
                    {
                        "partner_id": partners.id,
                        "line_ids": [(6, 0, lines.ids)],
                        "amount": sum(lines.mapped("amount_residual")),
                        "currency_id": currencies.id,
                        "company_id": companies.id,
                    }
                )
        session = self.env["pos.session"].search(
            [("state", "in", ("opening_control", "opened"))],
            order="id desc",
            limit=1,
        )
        if session:
            values.setdefault("session_id", session.id)
            values.setdefault("currency_id", session.currency_id.id)
            values.setdefault("company_id", session.company_id.id)
            payment_method = session.config_id.payment_method_ids.filtered(
                lambda method: not method.is_pos_customer_credit
            )[:1]
            if payment_method:
                values.setdefault("payment_method_id", payment_method.id)
        return values

    @api.depends("session_id")
    def _compute_available_payment_method_ids(self):
        for wizard in self:
            payment_methods = wizard.session_id.config_id.payment_method_ids
            wizard.available_payment_method_ids = payment_methods.filtered(
                lambda method: not method.is_pos_customer_credit
            )

    @api.depends("line_ids.amount_residual")
    def _compute_amount_selected(self):
        for wizard in self:
            wizard.amount_selected = sum(wizard.line_ids.mapped("amount_residual"))

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.line_ids = self.env["pos.customer.credit.line"].search(
                [
                    ("partner_id", "=", self.partner_id.id),
                    ("state", "in", ("open", "partial")),
                ],
                order="date_order asc, id asc",
            )
            self.amount = sum(self.line_ids.mapped("amount_residual"))
        else:
            self.line_ids = False
            self.amount = 0.0

    @api.onchange("line_ids")
    def _onchange_line_ids(self):
        if self.line_ids:
            self.amount = sum(self.line_ids.mapped("amount_residual"))
            self.currency_id = self.line_ids[:1].currency_id
            self.company_id = self.line_ids[:1].company_id
        else:
            self.amount = 0.0

    @api.onchange("session_id")
    def _onchange_session_id(self):
        if self.session_id:
            self.currency_id = self.session_id.currency_id
            self.company_id = self.session_id.company_id
            if self.payment_method_id not in self.available_payment_method_ids:
                self.payment_method_id = self.available_payment_method_ids[:1]

    def action_register_payment(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("Seleccione al menos un ticket pendiente."))
        rounding = self.currency_id.rounding
        if float_compare(self.amount, 0.0, precision_rounding=rounding) <= 0:
            raise UserError(_("El importe a cobrar debe ser mayor que cero."))
        if (
            float_compare(
                self.amount,
                self.amount_selected,
                precision_rounding=rounding,
            )
            > 0
        ):
            raise UserError(
                _("El importe a cobrar no puede superar el pendiente seleccionado.")
            )
        result = self.env["pos.customer.credit.payment"].pos_register_credit_payment(
            self.partner_id.id,
            self.line_ids.ids,
            self.amount,
            self.payment_method_id.id,
            self.session_id.id,
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Cobro de deuda"),
            "res_model": "pos.customer.credit.payment",
            "view_mode": "form",
            "res_id": result["payment_id"],
            "target": "current",
        }
