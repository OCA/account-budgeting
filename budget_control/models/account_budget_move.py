# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountBudgetMove(models.Model):
    _name = "account.budget.move"
    _inherit = ["base.budget.move"]
    _description = "Account Budget Moves"

    move_id = fields.Many2one(
        comodel_name="account.move",
        related="move_line_id.move_id",
        readonly=True,
        store=True,
        index=True,
        help="Commit budget for this move_id",
    )
    move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        readonly=True,
        index=True,
        help="Commit budget for this move_line_id",
    )
