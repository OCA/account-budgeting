# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BudgetPeriod(models.Model):
    _inherit = "budget.period"

    expense = fields.Boolean(
        string="On Expense",
        compute="_compute_control_expense",
        store=True,
        readonly=False,
        help="Control budget on expense approved",
    )

    def _budget_info_query(self):
        query = super()._budget_info_query()
        query["info_cols"]["amount_expense"] = ("5_ex_commit", True)
        return query

    @api.depends("control_budget")
    def _compute_control_expense(self):
        for rec in self:
            rec.expense = rec.control_budget

    @api.model
    def _get_eligible_budget_period(self, date=False, doc_type=False):
        budget_period = super()._get_eligible_budget_period(date, doc_type)
        # Get period control budget.
        # if doctype is expense, check special control too.
        if doc_type == "expense":
            return budget_period.filtered(
                lambda l: (l.control_budget and l.expense)
                or (not l.control_budget and l.expense)
            )
        return budget_period
