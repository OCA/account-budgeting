# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class HRExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    budget_move_ids = fields.One2many(
        comodel_name="expense.budget.move",
        inverse_name="sheet_id",
    )

    def recompute_budget_move(self):
        self.mapped("expense_line_ids").recompute_budget_move()

    def _write(self, vals):
        """
        - UnCommit budget when state post
        - Cancel/Draft document should delete all budget commitment
        """
        res = super()._write(vals)
        if vals.get("state") in ("post", "cancel", "draft"):
            BudgetControl = self.env["budget.control"]
            expense_line = self.mapped("expense_line_ids")
            analytic_account_ids = expense_line.mapped("analytic_account_id")
            budget_control = BudgetControl.search(
                [("analytic_account_id", "in", analytic_account_ids.ids)]
            )
            if any(state != "done" for state in budget_control.mapped("state")):
                raise UserError(_("Analytic Account is not Controlled"))
            if vals.get("state") == "post":
                expense_line.uncommit_expense_budget()
            else:
                expense_line.commit_budget()
        return res

    def _check_budget_expense(self):
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget(doc.budget_move_ids, doc_type="expense")

    def action_submit_sheet(self):
        res = super().action_submit_sheet()
        self.flush()
        self._check_budget_expense()
        return res
