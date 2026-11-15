# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
from odoo import models


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    def _compute_matrix(self):
        # XLSX and PDF call this method directly. Cached ORM fields must never
        # replace an explicit access check at the computation boundary.
        self.check_access("read")
        return super()._compute_matrix()

    def drilldown(self, arg):
        self.check_access("read")
        return super().drilldown(arg)

    def print_pdf(self):
        self.check_access("read")
        return super().print_pdf()

    def export_xls(self):
        self.check_access("read")
        return super().export_xls()
