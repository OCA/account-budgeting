# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class HRExpense(models.Model):
    _inherit = "hr.expense"

    is_clearing = fields.Boolean(
        string="Clear Advance",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="This Expense is clearing advance",
    )
    advance_budget_move_ids = fields.One2many(
        comodel_name="advance.budget.move",
        inverse_name="expense_id",
    )

    def _budget_move_create(self, vals):
        self.ensure_one()
        new_vals = vals.copy()
        if not self.advance and not self.is_clearing:
            return super()._budget_move_create(vals)
        # Case : clearing we should decrease budget advance before increase
        if self.advance:
            budget_move = self.env["advance.budget.move"].create(new_vals)
            return budget_move
        # Convert debit to credit
        budget_move = False
        if new_vals["debit"]:
            new_vals["credit"] = new_vals["debit"]
            new_vals["debit"] = 0.0
            budget_move = self.env["advance.budget.move"].create(new_vals)
        super()._budget_move_create(vals)
        return budget_move

    def _budget_move_unlink(self):
        self.ensure_one()
        if not self.advance and not self.is_clearing:
            return super()._budget_move_unlink()
        if self.is_clearing:
            super()._budget_move_unlink()
        return self.advance_budget_move_ids.unlink()

    def _search_domain_expense(self):
        domain = super()._search_domain_expense()
        domain = domain and not self.advance
        return domain
