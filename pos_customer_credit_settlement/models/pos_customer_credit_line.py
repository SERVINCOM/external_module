# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class PosCustomerCreditLine(models.Model):
    _name = "pos.customer.credit.line"
    _description = "POS Customer Credit Line"
    _order = "date_order desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Referencia",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Cliente",
        required=True,
        index=True,
        check_company=True,
    )
    pos_order_id = fields.Many2one(
        comodel_name="pos.order",
        string="Ticket TPV origen",
        required=True,
        readonly=True,
        index=True,
    )
    session_id = fields.Many2one(
        comodel_name="pos.session",
        string="Sesión TPV origen",
        readonly=True,
        index=True,
    )
    config_id = fields.Many2one(
        comodel_name="pos.config",
        string="Punto de venta origen",
        readonly=True,
        index=True,
    )
    date_order = fields.Datetime(string="Fecha ticket", required=True, readonly=True)
    amount_total = fields.Monetary(string="Importe original", required=True)
    amount_paid = fields.Monetary(string="Importe cobrado", default=0.0)
    amount_residual = fields.Monetary(
        string="Pendiente",
        compute="_compute_amount_residual",
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moneda",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    state = fields.Selection(
        selection=[
            ("open", "Pendiente"),
            ("partial", "Parcial"),
            ("paid", "Pagado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="open",
        required=True,
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    note = fields.Text(string="Notas")
    payment_line_ids = fields.One2many(
        comodel_name="pos.customer.credit.payment.line",
        inverse_name="credit_line_id",
        string="Cobros aplicados",
        readonly=True,
    )

    @api.depends("amount_total", "amount_paid")
    def _compute_amount_residual(self):
        for line in self:
            line.amount_residual = line.amount_total - line.amount_paid

    @api.constrains("amount_total", "amount_paid")
    def _check_amounts(self):
        for line in self:
            rounding = line.currency_id.rounding
            if float_compare(line.amount_total, 0.0, precision_rounding=rounding) < 0:
                raise ValidationError(_("El importe original no puede ser negativo."))
            if float_compare(line.amount_paid, 0.0, precision_rounding=rounding) < 0:
                raise ValidationError(_("El importe cobrado no puede ser negativo."))
            if (
                float_compare(
                    line.amount_paid,
                    line.amount_total,
                    precision_rounding=rounding,
                )
                > 0
            ):
                raise ValidationError(
                    _("El importe cobrado no puede superar el importe original.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "pos.customer.credit.line"
                ) or _("New")
        lines = super().create(vals_list)
        lines._refresh_credit_state()
        return lines

    def write(self, vals):
        result = super().write(vals)
        if {"amount_total", "amount_paid"} & set(vals) and vals.get("state") != "cancelled":
            self.filtered(lambda line: line.state != "cancelled")._refresh_credit_state()
        return result

    def _refresh_credit_state(self):
        for line in self:
            rounding = line.currency_id.rounding
            if line.state == "cancelled":
                continue
            if float_is_zero(line.amount_paid, precision_rounding=rounding):
                line.state = "open"
            elif float_is_zero(line.amount_residual, precision_rounding=rounding):
                line.state = "paid"
            else:
                line.state = "partial"

    def _apply_payment_amount(self, amount):
        self.ensure_one()
        if self.state not in ("open", "partial"):
            raise UserError(_("La deuda %s no está pendiente.") % self.display_name)
        rounding = self.currency_id.rounding
        if float_compare(amount, 0.0, precision_rounding=rounding) <= 0:
            raise UserError(_("El importe aplicado debe ser mayor que cero."))
        amount_to_apply = min(amount, self.amount_residual)
        self.amount_paid += amount_to_apply
        self._refresh_credit_state()
        return amount_to_apply

    def action_cancel(self):
        manager_group = (
            "pos_customer_credit_settlement.group_pos_customer_credit_manager"
        )
        for line in self:
            if line.amount_paid and not self.env.user.has_group(manager_group):
                raise UserError(
                    _(
                        "Solo un responsable puede cancelar una deuda con "
                        "cobros aplicados."
                    )
                )
            line.state = "cancelled"

    def action_reopen(self):
        self.filtered(lambda line: line.state == "cancelled").write({"state": "open"})
        self._refresh_credit_state()

    def _pos_export_data(self):
        return [
            {
                "id": line.id,
                "name": line.name,
                "partner_id": line.partner_id.id,
                "partner_name": line.partner_id.display_name,
                "pos_order_id": line.pos_order_id.id,
                "pos_order_name": line.pos_order_id.name,
                "session_id": line.session_id.id,
                "session_name": line.session_id.name,
                "config_id": line.config_id.id,
                "config_name": line.config_id.display_name,
                "date_order": fields.Datetime.to_string(line.date_order),
                "amount_total": line.amount_total,
                "amount_paid": line.amount_paid,
                "amount_residual": line.amount_residual,
                "currency_id": line.currency_id.id,
                "state": line.state,
            }
            for line in self
        ]
