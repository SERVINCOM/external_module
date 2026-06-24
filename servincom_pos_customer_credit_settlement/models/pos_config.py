# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    enable_pos_customer_credit = fields.Boolean(
        string="Activar crédito de clientes TPV"
    )
    allow_pos_credit_settlement = fields.Boolean(
        string="Permitir cobro de deuda desde TPV"
    )
    pos_credit_payment_method_id = fields.Many2one(
        comodel_name="pos.payment.method",
        string="Método de pago de crédito por defecto",
        domain="[('is_pos_customer_credit', '=', True)]",
    )
    pos_credit_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Cuenta contable de crédito TPV",
        domain="[('deprecated', '=', False)]",
        help=(
            "Cuenta orientativa para conciliación posterior cuando la "
            "arquitectura contable estándar del TPV no deje enlazar "
            "directamente la deuda con el cobro."
        ),
    )
