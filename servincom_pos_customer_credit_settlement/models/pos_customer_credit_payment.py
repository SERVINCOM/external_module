# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero


class PosCustomerCreditPayment(models.Model):
    _name = "pos.customer.credit.payment"
    _description = "POS Customer Credit Payment"
    _order = "payment_date desc, id desc"
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
    session_id = fields.Many2one(
        comodel_name="pos.session",
        string="Sesión TPV",
        required=True,
        readonly=True,
        index=True,
    )
    config_id = fields.Many2one(
        comodel_name="pos.config",
        string="Punto de venta",
        required=True,
        readonly=True,
        index=True,
    )
    payment_method_id = fields.Many2one(
        comodel_name="pos.payment.method",
        string="Método de cobro",
        required=True,
        readonly=True,
    )
    amount = fields.Monetary(string="Importe", required=True, readonly=True)
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moneda",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    payment_date = fields.Datetime(
        string="Fecha de cobro",
        required=True,
        readonly=True,
        default=fields.Datetime.now,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Borrador"),
            ("posted", "Publicado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="draft",
        required=True,
        index=True,
    )
    line_ids = fields.One2many(
        comodel_name="pos.customer.credit.payment.line",
        inverse_name="payment_id",
        string="Deudas pagadas",
        readonly=True,
    )
    account_payment_id = fields.Many2one(
        comodel_name="account.payment",
        string="Pago contable",
        readonly=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Asiento contable",
        related="account_payment_id.move_id",
        store=True,
        readonly=True,
    )
    note = fields.Text(string="Notas")

    @api.constrains("amount")
    def _check_amount(self):
        for payment in self:
            if (
                float_compare(
                    payment.amount,
                    0.0,
                    precision_rounding=payment.currency_id.rounding,
                )
                <= 0
            ):
                raise ValidationError(_("El importe del cobro debe ser mayor que cero."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "pos.customer.credit.payment"
                ) or _("New")
        return super().create(vals_list)

    @api.model
    def pos_search_credit_customers(self, query="", limit=20):
        domain = [("pos_credit_customer", "=", True)]
        query = (query or "").strip()
        if query:
            search_domain = [
                "|",
                "|",
                "|",
                ("name", "ilike", query),
                ("vat", "ilike", query),
                ("phone", "ilike", query),
                ("ref", "ilike", query),
            ]
            domain = expression.AND([domain, search_domain])
        partners = self.env["res.partner"].search(domain, limit=limit, order="name")
        return [
            {
                "id": partner.id,
                "name": partner.display_name,
                "vat": partner.vat or "",
                "phone": partner.phone or partner.mobile or "",
                "ref": partner.ref or "",
                "total_due": partner.pos_credit_total_due,
                "ticket_count": partner.pos_credit_ticket_count,
            }
            for partner in partners
        ]

    @api.model
    def pos_get_credit_lines(self, partner_id):
        return self.env["res.partner"].sudo().get_pos_credit_lines(partner_id)

    @api.model
    def pos_get_credit_backend_url(self):
        action = self.env.ref(
            "servincom_pos_customer_credit_settlement.action_pos_customer_credit_line"
        )
        menu = self.env.ref(
            "servincom_pos_customer_credit_settlement.menu_pos_customer_credit_line"
        )
        return "/web#action=%s&model=pos.customer.credit.line&view_type=list&menu_id=%s" % (
            action.id,
            menu.id,
        )

    @api.model
    def pos_register_credit_payment(
        self, partner_id, credit_line_ids, amount, payment_method_id, session_id
    ):
        partner = self.env["res.partner"].browse(partner_id).exists()
        session = self.env["pos.session"].browse(session_id).exists()
        payment_method = self.env["pos.payment.method"].browse(payment_method_id).exists()
        if not partner:
            raise UserError(_("Cliente no encontrado."))
        if not partner.pos_credit_customer:
            raise UserError(_("El cliente no está autorizado para crédito TPV."))
        if not session:
            raise UserError(_("Sesión TPV no encontrada."))
        if session.state not in ("opened", "opening_control"):
            raise UserError(_("La sesión TPV debe estar abierta para registrar cobros."))
        if not session.config_id.allow_pos_credit_settlement:
            raise UserError(
                _("Este punto de venta no permite cobrar deuda de clientes.")
            )
        if not payment_method:
            raise UserError(_("Método de cobro no encontrado."))
        if payment_method.is_pos_customer_credit:
            raise UserError(_("No puede cobrar una deuda usando otro método de crédito."))
        if payment_method not in session.config_id.payment_method_ids:
            raise UserError(
                _("El método de cobro no pertenece al punto de venta activo.")
            )
        amount = float(amount or 0.0)
        rounding = session.currency_id.rounding
        if float_compare(amount, 0.0, precision_rounding=rounding) <= 0:
            raise UserError(_("El importe a cobrar debe ser mayor que cero."))
        lines = self.env["pos.customer.credit.line"].sudo().search(
            [
                ("id", "in", credit_line_ids or []),
                ("partner_id", "=", partner.id),
                ("state", "in", ("open", "partial")),
            ],
            order="date_order asc, id asc",
        )
        if not lines:
            raise UserError(_("Seleccione al menos una deuda pendiente."))
        total_selected = sum(lines.mapped("amount_residual"))
        if float_compare(amount, total_selected, precision_rounding=rounding) > 0:
            raise UserError(_("El importe no puede superar el pendiente seleccionado."))

        payment = self.sudo().create(
            {
                "partner_id": partner.id,
                "session_id": session.id,
                "config_id": session.config_id.id,
                "payment_method_id": payment_method.id,
                "amount": amount,
                "currency_id": session.currency_id.id,
                "company_id": session.company_id.id,
            }
        )
        remaining = amount
        payment_line_model = self.env["pos.customer.credit.payment.line"].sudo()
        for credit_line in lines:
            if float_is_zero(remaining, precision_rounding=rounding):
                break
            applied = credit_line._apply_payment_amount(remaining)
            payment_line_model.create(
                {
                    "payment_id": payment.id,
                    "credit_line_id": credit_line.id,
                    "amount": applied,
                    "currency_id": payment.currency_id.id,
                    "company_id": payment.company_id.id,
                }
            )
            remaining -= applied

        payment._create_account_payment_if_possible()
        payment.state = "posted"
        payment._reconcile_credit_if_possible()
        return {
            "payment_id": payment.id,
            "name": payment.name,
            "amount": payment.amount,
            "partner_id": partner.id,
            "remaining_due": partner.pos_credit_total_due,
            "lines": self.pos_get_credit_lines(partner.id),
        }

    def _create_account_payment_if_possible(self):
        for payment in self:
            journal = payment.payment_method_id.journal_id
            if not journal:
                payment.note = _(
                    "No se creó pago contable porque el método de cobro no "
                    "tiene diario configurado."
                )
                continue
            payment_method_line = journal.inbound_payment_method_line_ids[:1]
            vals = {
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": payment.partner_id.id,
                "amount": payment.amount,
                "currency_id": payment.currency_id.id,
                "journal_id": journal.id,
                "date": fields.Date.context_today(payment),
                "ref": payment.name,
            }
            if payment_method_line:
                vals["payment_method_line_id"] = payment_method_line.id
            account_payment = self.env["account.payment"].create(vals)
            account_payment.action_post()
            payment.account_payment_id = account_payment.id

    def _reconcile_credit_if_possible(self):
        receivable_types = ("asset_receivable", "receivable")
        for payment in self.filtered("account_payment_id"):
            payment_lines = payment.account_payment_id.move_id.line_ids.filtered(
                lambda line: line.account_id.account_type in receivable_types
                and line.partner_id == payment.partner_id
                and not line.reconciled
            )
            if not payment_lines:
                continue
            for credit_line in payment.line_ids.mapped("credit_line_id"):
                move = credit_line.pos_order_id.account_move
                if not move:
                    continue
                order_lines = move.line_ids.filtered(
                    lambda line: line.account_id.account_type in receivable_types
                    and line.partner_id == payment.partner_id
                    and not line.reconciled
                )
                if order_lines:
                    try:
                        (payment_lines + order_lines).reconcile()
                    except Exception as error:
                        payment.note = "%s\n%s" % (
                            payment.note or "",
                            _(
                                "No se pudo conciliar automáticamente con %s: %s"
                            )
                            % (credit_line.display_name, error),
                        )

    def action_cancel(self):
        manager_group = (
            "servincom_pos_customer_credit_settlement.group_pos_customer_credit_manager"
        )
        if not self.env.user.has_group(manager_group):
            raise UserError(_("Solo un responsable puede cancelar cobros."))
        for payment in self:
            if payment.account_payment_id and payment.account_payment_id.state == "posted":
                payment.account_payment_id.action_draft()
                payment.account_payment_id.action_cancel()
            for line in payment.line_ids:
                credit_line = line.credit_line_id
                credit_line.amount_paid -= line.amount
                credit_line._refresh_credit_state()
            payment.state = "cancelled"


class PosCustomerCreditPaymentLine(models.Model):
    _name = "pos.customer.credit.payment.line"
    _description = "POS Customer Credit Payment Line"
    _order = "id"
    _check_company_auto = True

    payment_id = fields.Many2one(
        comodel_name="pos.customer.credit.payment",
        string="Cobro",
        required=True,
        ondelete="cascade",
        check_company=True,
    )
    credit_line_id = fields.Many2one(
        comodel_name="pos.customer.credit.line",
        string="Deuda",
        required=True,
        ondelete="restrict",
        check_company=True,
    )
    amount = fields.Monetary(string="Importe aplicado", required=True)
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
