# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, time

from odoo import models


class IgicBookXlsx(models.AbstractModel):
    _name = "report.servincom_igic_book.igic_book_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "SERVINCOM IGIC Excel book"

    def generate_xlsx_report(self, workbook, data, books):
        workbook.strings_to_formulas = False
        workbook.strings_to_urls = False
        title = workbook.add_format(
            {"bold": True, "font_size": 18, "font_color": "#153B54"}
        )
        header = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#153B54",
                "font_color": "#FFFFFF",
                "text_wrap": True,
            }
        )
        text = workbook.add_format({"valign": "top", "text_wrap": True})
        number = workbook.add_format(
            {"num_format": "#,##0.00;[Red]-#,##0.00", "valign": "top"}
        )
        date_format = workbook.add_format({"num_format": "dd/mm/yyyy", "valign": "top"})
        total = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#EAF1F5",
                "num_format": "#,##0.00;[Red]-#,##0.00",
            }
        )
        for book_index, book in enumerate(books, 1):
            sections = book._get_igic_report_sections()
            for section in sections:
                suffix = "" if len(books) == 1 else " %s" % book_index
                sheet = workbook.add_worksheet(
                    section["title"][: 31 - len(suffix)] + suffix
                )
                sheet.set_landscape()
                sheet.set_paper(9)
                sheet.fit_to_pages(1, 0)
                sheet.repeat_rows(0, 5)
                sheet.set_footer("&LSERVINCOM SOLUCIONES&R&P / &N")
                sheet.merge_range(0, 0, 0, 14, self.env._("IGIC invoice book"), title)
                sheet.merge_range(
                    1,
                    0,
                    1,
                    14,
                    "%s · %s" % (book.company_id.name, book.company_id.vat or ""),
                    text,
                )
                sheet.merge_range(
                    2,
                    0,
                    2,
                    14,
                    "%s — %s · %s · %s"
                    % (
                        book._format_date(book.date_start),
                        book._format_date(book.date_end),
                        book.currency_id.name,
                        section["title"],
                    ),
                    text,
                )
                sheet.merge_range(
                    3,
                    0,
                    3,
                    14,
                    self.env._("Accounting review report. Not an ATC filing file."),
                    text,
                )
                if book.state != "done" or book.error_count:
                    sheet.merge_range(
                        4,
                        0,
                        4,
                        14,
                        self.env._("Draft / review book warnings before use."),
                        text,
                    )
                headings = [
                    self.env._("No."),
                    self.env._("Invoice date"),
                    self.env._("Accounting date"),
                    self.env._("Invoice reference"),
                    self.env._("Supplier reference"),
                    self.env._("Partner"),
                    self.env._("VAT number"),
                    self.env._("Tax / operation"),
                    self.env._("Rate %"),
                    self.env._("Tax base"),
                    self.env._("IGIC / surcharge"),
                    self.env._("Deductible fee"),
                    self.env._("Non-deductible fee"),
                    self.env._("Refund"),
                    self.env._("Warning"),
                ]
                for col, label in enumerate(headings):
                    sheet.write_string(5, col, label, header)
                sheet.set_row(5, 32)
                sheet.set_column(0, 0, 7)
                sheet.set_column(1, 2, 13)
                sheet.set_column(3, 4, 23)
                sheet.set_column(5, 5, 32)
                sheet.set_column(6, 6, 18)
                sheet.set_column(7, 7, 30)
                sheet.set_column(8, 12, 16)
                sheet.set_column(13, 13, 10)
                sheet.set_column(14, 14, 32)
                sheet.freeze_panes(6, 5)
                for index, row in enumerate(section["rows"], 6):
                    sheet.write_number(index, 0, row["number"])
                    for col, key in ((1, "date"), (2, "accounting_date")):
                        if row[key]:
                            sheet.write_datetime(
                                index,
                                col,
                                datetime.combine(row[key], time.min),
                                date_format,
                            )
                    for col, key in (
                        (3, "reference"),
                        (4, "external_reference"),
                        (5, "partner"),
                        (6, "vat"),
                        (7, "tax"),
                        (14, "warning"),
                    ):
                        # Preserve NIFs/leading zeroes and prevent formula injection.
                        sheet.write_string(index, col, row[key], text)
                    for col, key in ((8, "rate"), (9, "base"), (10, "fee")):
                        sheet.write_number(index, col, row[key], number)
                    if section["kind"] == "received":
                        sheet.write_number(index, 11, row["deductible"], number)
                        sheet.write_number(
                            index, 12, row["fee"] - row["deductible"], number
                        )
                    sheet.write_string(
                        index, 13, self.env._("Yes") if row["refund"] else "", text
                    )
                end = 5 + len(section["rows"])
                sheet.autofilter(5, 0, max(end, 6), 14)
                row_index = max(end + 2, 8)
                sheet.merge_range(
                    row_index,
                    0,
                    row_index,
                    8,
                    self.env._("Totals without duplicate bases"),
                    header,
                )
                sheet.write_number(row_index, 9, section["base"], total)
                sheet.write_number(row_index, 10, section["fee"], total)
                if section["kind"] == "received":
                    sheet.write_number(row_index, 11, section["deductible"], total)
                    sheet.write_number(
                        row_index, 12, section["fee"] - section["deductible"], total
                    )
                row_index += 3
                sheet.merge_range(
                    row_index, 0, row_index, 7, self.env._("Tax summary"), title
                )
                row_index += 1
                for col, label in (
                    (7, "Tax / operation"),
                    (8, "Rate %"),
                    (9, "Tax base"),
                    (10, "IGIC / surcharge"),
                    (11, "Deductible fee"),
                ):
                    sheet.write_string(row_index, col, self.env._(label), header)
                for row in section["summary"]:
                    row_index += 1
                    sheet.write_string(row_index, 7, row["tax"], text)
                    for col, key in ((8, "rate"), (9, "base"), (10, "fee")):
                        sheet.write_number(row_index, col, row[key], number)
                    if section["kind"] == "received":
                        sheet.write_number(row_index, 11, row["deductible"], number)
                sheet.print_area(0, 0, row_index + 1, 14)
