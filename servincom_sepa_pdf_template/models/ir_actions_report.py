# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from collections import OrderedDict
from io import BytesIO

from odoo import models

from ..pdf_form import PdfTemplateError

_logger = logging.getLogger(__name__)
SEPA_REPORT = "account_banking_sepa_direct_debit.report_sepa_direct_debit_mandate"


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        report = self._get_report(report_ref)
        target = self.env.ref(SEPA_REPORT, raise_if_not_found=False)
        if not target or report.id != target.id or not res_ids:
            return super()._render_qweb_pdf_prepare_streams(
                report_ref, data, res_ids=res_ids
            )
        streams = OrderedDict()
        for res_id in dict.fromkeys(res_ids):
            mandate = self.env["account.banking.mandate"].browse(res_id)
            mandate.check_access("read")
            try:
                content = mandate._sepa_render_custom_pdf()
            except PdfTemplateError:
                # Avoid logging customer data, PDF contents or bank information.
                _logger.warning(
                    "Custom SEPA PDF failed for mandate id=%s; using OCA report", res_id
                )
                content = False
            if content:
                streams[res_id] = {"stream": BytesIO(content), "attachment": None}
            else:
                original = super()._render_qweb_pdf_prepare_streams(
                    report_ref, data, res_ids=[res_id]
                )
                streams[res_id] = original.get(res_id) or original[False]
        return streams
