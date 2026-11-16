# Copyright 2026 SERVINCOM SOLUCIONES, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "SERVINCOM Accounting Dashboards",
    "summary": "Monthly results and account detail with explicit user access",
    "version": "18.0.1.5.1",
    "license": "AGPL-3",
    "author": "SERVINCOM SOLUCIONES, S.L.",
    "website": "https://www.servincom.com",
    "category": "Accounting/Reporting",
    "depends": ["mis_builder", "account_financial_report", "board"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "security/rules.xml",
        "data/report_templates.xml",
        "views/dashboard_views.xml",
        "views/res_users_views.xml",
        "views/report_layout.xml",
        "views/account_maturity_views.xml",
        "views/dashboard_analysis_views.xml",
        "views/customer_history_views.xml",
    ],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "servincom_account_dashboard/static/src/js/dashboard_card.js",
            "servincom_account_dashboard/static/src/js/dashboard_board.js",
            "servincom_account_dashboard/static/src/xml/dashboard_board.xml",
            "servincom_account_dashboard/static/src/js/dashboard_analysis.js",
            "servincom_account_dashboard/static/src/xml/dashboard_analysis.xml",
            "servincom_account_dashboard/static/src/scss/dashboard.scss",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
