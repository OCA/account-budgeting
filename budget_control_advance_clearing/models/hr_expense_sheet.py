# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class HRExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    advance_budget_move_ids = fields.One2many(
        comodel_name="advance.budget.move",
        inverse_name="sheet_id",
    )
    is_clearing = fields.Boolean(
        string="Clearing", compute="_compute_clearing", store=True
    )

    def _write(self, vals):
        res = super()._write(vals)
        expense_line = self.mapped("expense_line_ids")
        if vals.get("state") == "done" and vals.get("advance_sheet_residual"):
            expense_line.uncommit_expense_budget()
        return res

    @api.depends("expense_line_ids")
    def _compute_clearing(self):
        for sheet in self:
            sheet.is_clearing = bool(sheet.expense_line_ids.filtered("is_clearing"))
        return

    def _check_budget_expense(self):
        if any(not exp.advance for exp in self):
            return super()._check_budget_expense()
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget(doc.advance_budget_move_ids, doc_type="advance")

    def recompute_advance_budget_move(self):
        self.mapped("advance_budget_move_ids").unlink()
        self.commit_budget()
        self.uncommit_expense_budget()

    def action_sheet_move_create(self):
        res = super().action_sheet_move_create()
        for sheet in self.filtered(lambda l: l.advance):
            sheet.account_move_id.write({"not_affect_budget": True})
        return res
