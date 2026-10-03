# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..pdf_form import PdfTemplateError


class SepaPdfPreview(models.TransientModel):
    _name = "servincom.sepa.pdf.preview"
    _description = "SEPA PDF preview"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    mandate_id = fields.Many2one(
        "account.banking.mandate", string="Mandate", required=True, check_company=True
    )
    scheme = fields.Selection(related="mandate_id.scheme", string="SEPA scheme")
    template_name = fields.Char(
        string="Selected PDF template", compute="_compute_template_name"
    )
    pdf_file = fields.Binary(string="Generated PDF", readonly=True, attachment=True)
    filename = fields.Char(string="PDF filename", readonly=True)

    @api.depends("mandate_id", "company_id")
    def _compute_template_name(self):
        for wizard in self:
            wizard.template_name = False
            if wizard.mandate_id and wizard.mandate_id.company_id == wizard.company_id:
                wizard.template_name = wizard.mandate_id._sepa_pdf_template(
                    preview=True
                )[1]

    def action_preview(self):
        self.ensure_one()
        self.check_access("write")
        self.company_id._sepa_check_manager()
        if self.mandate_id.company_id != self.company_id:
            raise ValidationError(
                self.env._("The mandate must belong to the selected company.")
            )
        try:
            pdf = self.mandate_id._sepa_render_custom_pdf(preview=True)
        except PdfTemplateError as exc:
            raise ValidationError(
                self.env._(
                    "The selected PDF template is invalid. Validate it in Settings."
                )
            ) from exc
        if not pdf:
            raise ValidationError(
                self.env._("No PDF template is configured for this company and scheme.")
            )
        self.write(
            {
                "pdf_file": base64.b64encode(pdf),
                "filename": self.mandate_id.sepa_pdf_download_name() + ".pdf",
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content?model=servincom.sepa.pdf.preview&id=%s&field=pdf_file&filename_field=filename&download=true"
            % self.id,
            "target": "self",
        }
