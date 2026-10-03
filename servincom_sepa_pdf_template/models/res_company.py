# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

from ..pdf_form import inspect_template

MANAGERS = "account.group_account_manager,base.group_system"
TEMPLATE_FIELDS = {
    "sepa_pdf_enabled",
    "sepa_pdf_core",
    "sepa_pdf_core_filename",
    "sepa_pdf_b2b",
    "sepa_pdf_b2b_filename",
}
AUDIT_FIELDS = {
    "sepa_pdf_validation_result",
    "sepa_pdf_validation_date",
    "sepa_pdf_validation_user_id",
}


class ResCompany(models.Model):
    _inherit = "res.company"

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
        string="Last PDF validation", readonly=True, groups=MANAGERS
    )
    sepa_pdf_validation_date = fields.Datetime(
        string="Validation date", readonly=True, groups=MANAGERS
    )
    sepa_pdf_validation_user_id = fields.Many2one(
        "res.users", string="Validated by", readonly=True, groups=MANAGERS
    )

    def _sepa_check_manager(self):
        if not (
            self.env.su
            or self.env.user.has_group("account.group_account_manager")
            or self.env.user.has_group("base.group_system")
        ):
            raise AccessError(
                _("Only accounting managers or administrators can configure SEPA PDFs.")
            )
        if not self.env.su and any(
            company not in self.env.companies for company in self
        ):
            raise AccessError(
                _("Select an allowed company before configuring its SEPA PDF.")
            )

    def _sepa_pdf_diagnostics(self):
        self.ensure_one()
        messages, valid, present = [], True, False
        for scheme in ("core", "b2b"):
            binary = self.with_context(bin_size=False)["sepa_pdf_" + scheme]
            if not binary:
                continue
            present = True
            try:
                result = inspect_template(base64.b64decode(binary, validate=True))
            except (ValueError, TypeError):
                result = {
                    "valid": False,
                    "found": [],
                    "missing": [],
                    "unknown": [],
                    "errors": ["invalid"],
                }
            valid = valid and result["valid"]
            messages.append(
                _(
                    "%(scheme)s - Found: %(found)s\nMissing: %(missing)s\nUnknown: %(unknown)s",
                    scheme=scheme.upper(),
                    found=", ".join(result["found"]) or "-",
                    missing=", ".join(result["missing"]) or "-",
                    unknown=", ".join(result["unknown"]) or "-",
                )
            )
            for error in result["errors"]:
                if error == "flat":
                    messages.append(
                        _(
                            "The selected file is a flat PDF. To use it as a SEPA template it must contain PDF form fields with the required standardized names."
                        )
                    )
                elif error == "runtime":
                    messages.append(
                        _(
                            "The installed pypdf version does not support flattening. Install pypdf 6.10.0 or a compatible version."
                        )
                    )
                elif error.startswith("field:"):
                    messages.append(
                        _(
                            "Invalid field type, appearance or visible widget: %s",
                            error.split(":", 1)[1],
                        )
                    )
                else:
                    messages.append(
                        _(
                            "Invalid PDF: use an unsigned, unencrypted AcroForm, at most 10 MiB and 20 pages, without XFA."
                        )
                    )
        if not present:
            messages.append(_("Upload at least one CORE or B2B PDF template."))
        messages.append(
            _("PDF validation successful.")
            if valid and present
            else _("PDF validation failed. Custom templates cannot be enabled.")
        )
        return valid and present, "\n\n".join(messages)

    def _sepa_record_validation(self):
        for company in self:
            valid, message = company._sepa_pdf_diagnostics()
            if company.sepa_pdf_enabled and not valid:
                raise ValidationError(message)
            super(ResCompany, company).write(
                {
                    "sepa_pdf_validation_result": message,
                    "sepa_pdf_validation_date": fields.Datetime.now(),
                    "sepa_pdf_validation_user_id": self.env.uid,
                }
            )

    @api.model_create_multi
    def create(self, vals_list):
        if any(AUDIT_FIELDS.intersection(vals) for vals in vals_list):
            raise AccessError(_("PDF validation history is managed automatically."))
        if any(TEMPLATE_FIELDS.intersection(vals) for vals in vals_list):
            self._sepa_check_manager()
        companies = super().create(vals_list)
        for company, vals in zip(companies, vals_list, strict=True):
            if TEMPLATE_FIELDS.intersection(vals):
                company._sepa_record_validation()
        return companies

    def write(self, vals):
        if AUDIT_FIELDS.intersection(vals):
            raise AccessError(_("PDF validation history is managed automatically."))
        changed = TEMPLATE_FIELDS.intersection(vals)
        if changed:
            self._sepa_check_manager()
        result = super().write(vals)
        if changed:
            self._sepa_record_validation()
        return result
