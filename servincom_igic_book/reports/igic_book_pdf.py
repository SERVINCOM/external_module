# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class IgicBookPdf(models.AbstractModel):
    _name = "report.servincom_igic_book.report_igic_book"
    _description = "SERVINCOM IGIC PDF book"

    @api.model
    def _get_report_values(self, docids, data=None):
        books = self.env["l10n.es.vat.book"].browse(docids)
        sections = {book.id: book._get_igic_report_sections() for book in books}
        return {
            "doc_ids": books.ids,
            "doc_model": books._name,
            "docs": books,
            "sections": sections,
        }
