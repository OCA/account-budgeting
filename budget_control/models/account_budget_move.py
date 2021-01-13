# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountBudgetMove(models.Model):
    _name = "account.budget.move"
    _inherit = ["base.budget.move"]
    _description = "Account Budget Moves"

    move_id = fields.Many2one(
        comodel_name="account.move",
    )
    move_line_id = fields.Many2one(comodel_name="account.move.line")
