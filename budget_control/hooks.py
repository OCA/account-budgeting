# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import SUPERUSER_ID, api


def update_data_hooks(cr, registry):

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Enable Analytic Account
        env.ref("base.group_user").write(
            {"implied_ids": [(4, env.ref("analytic.group_analytic_accounting").id)]}
        )


def uninstall_hook(cr, registry):
    """Delete all data related to budget control"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    periods = env["budget.period"].search([])
    instances = periods.mapped("report_instance_id")
    buget_controls = env["budget.control"].search([])
    budgets = buget_controls.mapped("budget_id")
    periods.unlink()
    budgets.unlink()
    buget_controls.unlink()
    instances.unlink()
    env.ref("budget_control.budget_kpi").unlink()
