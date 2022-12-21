# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AdvanceBudgetMove(models.Model):
    _name = "advance.budget.move"
    _inherit = ["expense.budget.move"]
    _description = "Advance Budget Moves"

    clearing_id = fields.Many2one(
        comodel_name="hr.expense",
        readonly=True,
        index=True,
        help="Reference to clearing that uncommit this",
    )
