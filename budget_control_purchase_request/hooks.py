# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["budget.period"].search([])._recompute_report_instance_periods()


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    model = env.ref(
        "budget_control_purchase_request.model_purchase_request_budget_move"
    )
    periods = env["mis.report.instance.period"].search(
        [
            ("source_aml_model_id", "=", model.id),
        ]
    )
    for period in periods:
        period.report_instance_id.period_ids.mapped("source_sumcol_ids").filtered(
            lambda l: l.period_to_sum_id == period
        ).unlink()
    periods.unlink()
