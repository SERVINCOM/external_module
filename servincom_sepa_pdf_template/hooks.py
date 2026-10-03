# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json

REPORT = "account_banking_sepa_direct_debit.report_sepa_direct_debit_mandate"
BACKUP = "servincom_sepa_pdf_template.previous_filename"
EXPRESSION = "object.sepa_pdf_download_name()"


def post_init_hook(env):
    report = env.ref(REPORT)
    env["ir.config_parameter"].sudo().set_param(
        BACKUP, json.dumps(report.print_report_name)
    )
    report.write({"print_report_name": EXPRESSION})


def uninstall_hook(env):
    report = env.ref(REPORT, raise_if_not_found=False)
    params = env["ir.config_parameter"].sudo()
    previous = params.get_param(BACKUP)
    if report and previous and report.print_report_name == EXPRESSION:
        report.write({"print_report_name": json.loads(previous)})
    params.search([("key", "=", BACKUP)]).unlink()
