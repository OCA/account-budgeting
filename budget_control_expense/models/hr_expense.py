# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class HRExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    budget_move_ids = fields.One2many(
        comodel_name="expense.budget.move",
        inverse_name="sheet_id",
    )

    @api.constrains("expense_line_ids")
    def recompute_budget_move(self):
        self.mapped("expense_line_ids").recompute_budget_move()

    def close_budget_move(self):
        self.mapped("expense_line_ids").close_budget_move()

    def write(self, vals):
        """
        - UnCommit budget when state post
        - Cancel/Draft document should delete all budget commitment
        """
        res = super().write(vals)
        if vals.get("state") in ("approve", "cancel", "draft"):
            doclines = self.mapped("expense_line_ids")
            if vals.get("state") in ("cancel", "draft"):
                doclines.write({"date_commit": False})
            doclines.recompute_budget_move()
        return res

    def approve_expense_sheets(self):
        res = super().approve_expense_sheets()
        self.flush()
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget(doc.expense_line_ids, doc_type="expense")
        return res

    def action_submit_sheet(self):
        res = super().action_submit_sheet()
        self.flush()
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget_precommit(
                doc.expense_line_ids, doc_type="expense"
            )
        return res

    def action_sheet_move_create(self):
        res = super().action_sheet_move_create()
        self.flush()
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget(doc.account_move_id.line_ids)
        return res


class HRExpense(models.Model):
    _name = "hr.expense"
    _inherit = ["hr.expense", "budget.docline.mixin"]
    _budget_date_commit_fields = ["sheet_id.write_date"]
    _budget_move_model = "expense.budget.move"
    _doc_rel = "sheet_id"

    budget_move_ids = fields.One2many(
        comodel_name="expense.budget.move",
        inverse_name="expense_id",
    )

    def recompute_budget_move(self):
        MoveLine = self.env["account.move.line"]
        for expense in self:
            expense[self._budget_field()].unlink()
            expense.commit_budget()
            move_lines = MoveLine.search([("expense_id", "in", expense.ids)])
            move_lines.uncommit_expense_budget()
            expense.forward_commit()

    def _init_docline_budget_vals(self, budget_vals):
        self.ensure_one()
        if not budget_vals.get("amount_currency", False):  # case clear advance
            budget_vals["amount_currency"] = self.quantity * self.unit_amount
            budget_vals["tax_ids"] = self.tax_ids.ids
        # Document specific vals
        budget_vals.update(
            {
                "expense_id": self.id,
                "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
            }
        )
        return super()._init_docline_budget_vals(budget_vals)

    def _valid_commit_state(self):
        states = ["approved", "done"]
        return self.state in states

    def _get_account_move_line_values(self):
        move_line_values_by_expense = super()._get_account_move_line_values()
        for expense in self:
            for ml in move_line_values_by_expense[expense.id]:
                if ml.get("analytic_account_id") and expense.fwd_analytic_account_id:
                    ml["analytic_account_id"] = expense.fwd_analytic_account_id.id
        return move_line_values_by_expense

    def _prepare_move_values(self):
        move_values = super()._prepare_move_values()
        journal = self.env["account.journal"].browse(move_values["journal_id"])
        move_values["not_affect_budget"] = journal.not_affect_budget
        return move_values

    def _get_included_tax(self):
        if self._name == "hr.expense":
            return self.env.company.budget_include_tax_expense
        return super()._get_included_tax()