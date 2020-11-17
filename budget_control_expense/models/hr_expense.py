# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


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
        - Commit budget when state approved
        - Cancel/Draft document should delete all budget commitment
        """
        res = super()._write(vals)
        if vals.get("state") in ("approve", "cancel", "draft"):
            self.mapped("expense_line_ids").commit_budget()
        elif vals.get("state") == "post":
            self.mapped("expense_line_ids").uncommit_expense_budget()
        return res

    def approve_expense_sheets(self):
        res = super().approve_expense_sheets()
        self.flush()
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget(doc.budget_move_ids, doc_type="expense")
        return res


class HRExpense(models.Model):
    _name = "hr.expense"
    _inherit = ["hr.expense", "budget.docline.mixin"]

    budget_move_ids = fields.One2many(
        comodel_name="expense.budget.move",
        inverse_name="expense_id",
    )

    def recompute_budget_move(self):
        self.mapped("budget_move_ids").unlink()
        self.commit_budget()
        self.uncommit_expense_budget()

    def commit_budget(self, reverse=False):
        """Create budget commit for each expense."""
        for expense in self:
            if expense.state in ("approved", "done"):
                account = expense.account_id
                analytic_account = expense.analytic_account_id
                doc_date = expense.date
                amount_currency = expense.untaxed_amount
                currency = expense.currency_id
                vals = expense._prepare_budget_commitment(
                    account,
                    analytic_account,
                    doc_date,
                    amount_currency,
                    currency,
                    reverse=reverse,
                )
                # Document specific vals
                vals.update(
                    {
                        "expense_id": expense.id,
                        "analytic_tag_ids": [(6, 0, expense.analytic_tag_ids.ids)],
                    }
                )
                self.env["expense.budget.move"].create(vals)
                if reverse:  # On reverse, make sure not over returned
                    self.env["budget.period"].check_over_returned_budget(self.sheet_id)
            else:
                expense.budget_move_ids.unlink()

    def uncommit_expense_budget(self):
        """For vendor bill in valid state, do uncommit for related expense."""
        for expense in self:
            if expense.sheet_id.state in ("post", "done") and expense.state in (
                "approved",
                "done",
            ):
                expense.commit_budget(reverse=True)
