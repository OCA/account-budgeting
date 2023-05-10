# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HRExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"
    _docline_rel = "expense_line_ids"
    _docline_type = "expense"

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
        Uncommit budget when the state is "approve" or cancel/draft the document.
        When the document is cancelled or drafted, delete all budget commitments.
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
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget(doc.expense_line_ids, doc_type="expense")
        return res

    def action_submit_sheet(self):
        res = super().action_submit_sheet()
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget_precommit(
                doc.expense_line_ids, doc_type="expense"
            )
        return res

    def action_sheet_move_create(self):
        res = super().action_sheet_move_create()
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
        for expense in self:
            # Make sure that date_commit not recompute
            ex_date_commit = expense.date_commit or self.env.context.get(
                "force_date_commit", False
            )
            expense[self._budget_field()].unlink()
            expense.with_context(force_date_commit=ex_date_commit).commit_budget()
            move_lines = expense.sheet_id.account_move_id.line_ids
            # credit will not over debit (auto adjust)
            expense.forward_commit()
            move_lines.uncommit_expense_budget()

    def _init_docline_budget_vals(self, budget_vals):
        self.ensure_one()
        if not budget_vals.get("amount_currency", False):
            budget_vals["amount_currency"] = (
                (self.quantity * self.unit_amount)
                if self.product_has_cost
                else self.total_amount
            )
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
        return self.state in ["approved", "done"]

    def _get_account_move_line_values(self):
        move_line_values_by_expense = super()._get_account_move_line_values()
        for expense in self:
            for ml in move_line_values_by_expense[expense.id]:
                if ml.get("analytic_account_id") and expense.fwd_analytic_account_id:
                    ml["analytic_account_id"] = expense.fwd_analytic_account_id.id
        return move_line_values_by_expense

    def _get_included_tax(self):
        if self._name == "hr.expense":
            return self.env.company.budget_include_tax_expense
        return super()._get_included_tax()
