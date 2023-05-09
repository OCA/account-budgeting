# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BudgetPeriod(models.Model):
    _inherit = "budget.period"

    purchase_request = fields.Boolean(
        string="On Purchase Request",
        compute="_compute_control_purchase_request",
        store=True,
        readonly=False,
        help="Control budget on purchase request approved",
    )

    def _budget_info_query(self):
        query = super()._budget_info_query()
        query["info_cols"]["amount_purchase_request"] = ("2_pr_commit", True)
        return query

    @api.depends("control_budget")
    def _compute_control_purchase_request(self):
        for rec in self:
            rec.purchase_request = rec.control_budget

    @api.model
    def _get_eligible_budget_period(self, date=False, doc_type=False):
        budget_period = super()._get_eligible_budget_period(date, doc_type)
        # Get period control budget.
        # if doctype is purchase_request, check special control too.
        if doc_type == "purchase_request":
            return budget_period.filtered(
                lambda l: (l.control_budget and l.purchase_request)
                or (not l.control_budget and l.purchase_request)
            )
        return budget_period
