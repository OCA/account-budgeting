# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    domain = "['|',('company_id','=',False),('company_id','in',company_ids)]"
    rule = env.ref("account_budget_oca.budget_post_comp_rule", raise_if_not_found=False)
    if rule:
        rule.write({"domain_force": domain})
    rule = env.ref("account_budget_oca.budget_comp_rule", raise_if_not_found=False)
    if rule:
        rule.write({"domain_force": domain})

    rule = env.ref(
        "account_budget_oca.budget_lines_comp_rule", raise_if_not_found=False
    )
    if rule:
        rule.write({"domain_force": domain})
