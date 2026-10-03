# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import re

from odoo import fields, models
from odoo.tools import format_date

from ..pdf_form import fill_template


class AccountBankingMandate(models.Model):
    _inherit = "account.banking.mandate"

    sepa_signature_city = fields.Char(string="Place of signature")

    def _sepa_pdf_values(self):
        self.ensure_one()
        company = self.company_id
        values = {
            "mandate_reference": self.unique_mandate_reference or "",
            "creditor_identifier": company.sepa_creditor_identifier or "",
            "creditor_name": company.name or "",
            "debtor_name": self.partner_id.name or "",
            "debtor_bic": self.partner_bank_id.bank_bic or "",
            "debtor_iban": self.partner_bank_id.acc_number or "",
            "payment_recurrent": self.type == "recurrent",
            "payment_oneoff": self.type == "oneoff",
            "date_location": "%s, %s"
            % (self.sepa_signature_city, format_date(self.env, self.signature_date))
            if self.signature_date and self.sepa_signature_city
            else "",
            "debtor_signature": "",
        }
        for prefix, partner in (
            ("creditor", company.partner_id),
            ("debtor", self.partner_id),
        ):
            values[prefix + "_address"] = ", ".join(
                filter(None, [partner.street, partner.street2])
            )
            values[prefix + "_postal_city_state"] = " · ".join(
                filter(None, [partner.zip, partner.city, partner.state_id.name])
            )
            values[prefix + "_country"] = partner.country_id.name or ""
        return values

    def _sepa_pdf_template(self, preview=False):
        self.ensure_one()
        self.check_access("read")
        # Sudo reads only this mandate's company configuration, after access checks.
        company = self.company_id.sudo().with_context(bin_size=False)
        if (
            self.format != "sepa"
            or self.scheme not in ("CORE", "B2B")
            or (not preview and not company.sepa_pdf_enabled)
        ):
            return False, False
        scheme = self.scheme.lower()
        return company["sepa_pdf_" + scheme], company[
            "sepa_pdf_" + scheme + "_filename"
        ]

    def _sepa_render_custom_pdf(self, preview=False):
        self.ensure_one()
        binary, filename = self._sepa_pdf_template(preview=preview)
        if not binary:
            return False
        from ..pdf_form import PdfTemplateError

        try:
            content = base64.b64decode(binary, validate=True)
        except (ValueError, TypeError) as exc:
            raise PdfTemplateError("Invalid encoded template") from exc
        return fill_template(content, self._sepa_pdf_values())

    def sepa_pdf_download_name(self):
        self.ensure_one()
        name = "Mandato-%s-%s" % (
            self.unique_mandate_reference or "",
            self.partner_id.name or "",
        )
        return re.sub(r'[\x00-\x1f/\\:*?"<>|]', "_", name)[:180]
