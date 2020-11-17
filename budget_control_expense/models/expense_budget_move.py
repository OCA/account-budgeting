# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ExpenseBudgetMove(models.Model):
    _name = "expense.budget.move"
    _inherit = ["base.budget.move"]
    _description = "Expense Budget Moves"

    expense_id = fields.Many2one(
        comodel_name="hr.expense",
        readonly=True,
        index=True,
        help="Commit budget for this expense_id",
    )
    sheet_id = fields.Many2one(
        comodel_name="hr.expense.sheet",
        related="expense_id.sheet_id",
        readonly=True,
        store=True,
        index=True,
    )
