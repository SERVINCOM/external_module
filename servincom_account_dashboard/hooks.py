# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
def post_init_hook(env):
    for company in env["res.company"].search([]):
        env["servincom.account.dashboard"].with_company(company)._ensure_company_dashboard()
