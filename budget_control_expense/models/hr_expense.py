# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class HRExpense(models.Model):
    _name = "hr.expense"
    _inherit = ["hr.expense", "budget.docline.mixin"]

    budget_move_ids = fields.One2many(
        comodel_name="expense.budget.move",
        inverse_name="expense_id",
    )

    def _write(self, vals):
        """
        - Commit budget when state submitted
        """
        res = super()._write(vals)
        if vals.get("state") == "reported":
            BudgetControl = self.env["budget.control"]
            budget_control = BudgetControl.search(
                [("analytic_account_id", "in", self.mapped("analytic_account_id").ids)]
            )
            if any(state != "done" for state in budget_control.mapped("state")):
                raise UserError(_("Analytic Account is not Controlled"))
            self.commit_budget()
        return res

    def recompute_budget_move(self):
        self.mapped("budget_move_ids").unlink()
        self.commit_budget()
        self.uncommit_expense_budget()

    def _budget_move_create(self, vals):
        self.ensure_one()
        budget_move = self.env["expense.budget.move"].create(vals)
        return budget_move

    def _budget_move_unlink(self):
        self.ensure_one()
        self.budget_move_ids.unlink()

    def commit_budget(self, reverse=False):
        """Create budget commit for each expense."""
        for expense in self:
            if expense.state in ("reported", "approved", "done"):
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
                expense._budget_move_create(vals)
                if reverse and not expense._context.get(
                    "force_check_reverse", False
                ):  # On reverse, make sure not over returned
                    self.env["budget.period"].check_over_returned_budget(self.sheet_id)
            else:
                expense._budget_move_unlink()

    def _search_domain_expense(self):
        domain = self.sheet_id.state in ("post", "done") and self.state in (
            "approved",
            "done",
        )
        return domain

    def uncommit_expense_budget(self):
        """For vendor bill in valid state, do uncommit for related expense."""
        for expense in self:
            domain = expense._search_domain_expense()
            if domain:
                expense.commit_budget(reverse=True)
