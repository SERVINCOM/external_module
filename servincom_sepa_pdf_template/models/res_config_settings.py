# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from .res_company import MANAGERS, TEMPLATE_FIELDS


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sepa_pdf_enabled = fields.Boolean(string="Enable custom SEPA PDF", groups=MANAGERS)
    sepa_pdf_core = fields.Binary(
        string="CORE PDF template", attachment=True, groups=MANAGERS
    )
    sepa_pdf_core_filename = fields.Char(string="CORE filename", groups=MANAGERS)
    sepa_pdf_b2b = fields.Binary(
        string="B2B PDF template", attachment=True, groups=MANAGERS
    )
    sepa_pdf_b2b_filename = fields.Char(string="B2B filename", groups=MANAGERS)
    sepa_pdf_validation_result = fields.Text(
        related="company_id.sepa_pdf_validation_result", groups=MANAGERS
    )
    sepa_pdf_validation_date = fields.Datetime(
        related="company_id.sepa_pdf_validation_date", groups=MANAGERS
    )
    sepa_pdf_validation_user_id = fields.Many2one(
        related="company_id.sepa_pdf_validation_user_id", groups=MANAGERS
    )

    @api.model
    def default_get(self, field_names):
        values = super().default_get(field_names)
        if self.env.user.has_group(
            "account.group_account_manager"
        ) or self.env.user.has_group("base.group_system"):
            company = self.env["res.company"].browse(
                values.get("company_id") or self.env.company.id
            )
            company._sepa_check_manager()
            for name in TEMPLATE_FIELDS.intersection(field_names):
                values[name] = company.sudo().with_context(bin_size=False)[name]
        return values

    @api.onchange("company_id")
    def _onchange_sepa_company(self):
        if self.env.user.has_group(
            "account.group_account_manager"
        ) or self.env.user.has_group("base.group_system"):
            for settings in self:
                settings.company_id._sepa_check_manager()
                for name in TEMPLATE_FIELDS:
                    settings[name] = settings.company_id.sudo().with_context(
                        bin_size=False
                    )[name]

    @api.onchange("sepa_pdf_core", "sepa_pdf_b2b")
    def _onchange_sepa_pdf_upload(self):
        self.company_id._sepa_check_manager()
        draft = self.env["res.company"].new(
            {
                "sepa_pdf_core": self.sepa_pdf_core,
                "sepa_pdf_b2b": self.sepa_pdf_b2b,
            }
        )
        valid, message = draft._sepa_pdf_diagnostics()
        return {"warning": {"title": self.env._("PDF validation"), "message": message}}

    def _sepa_save(self):
        self.ensure_one()
        self.company_id._sepa_check_manager()
        values = {
            name: self.with_context(bin_size=False)[name] for name in TEMPLATE_FIELDS
        }
        # Only the five SEPA settings are elevated, after manager and company checks.
        self.company_id.sudo().write(values)

    def set_values(self):
        result = super().set_values()
        self._sepa_save()
        return result

    def action_sepa_pdf_validate(self):
        self._sepa_save()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("PDF validation"),
                "message": self.company_id.sudo().sepa_pdf_validation_result,
                "sticky": True,
            },
        }

    def action_sepa_pdf_preview(self):
        self._sepa_save()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Preview SEPA mandate"),
            "res_model": "servincom.sepa.pdf.preview",
            "view_mode": "form",
            "target": "new",
            "context": {"default_company_id": self.company_id.id},
        }
