# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetControl(models.Model):
    _inherit = "budget.control"

    amount_advance = fields.Monetary(
        string="Advance",
        compute="_compute_budget_info",
        help="Sum of advance amount",
    )

    def get_move_commit(self, domain):
        budget_move = super().get_move_commit(domain)
        AdvanceBudgetMove = self.env["advance.budget.move"]
        advance_move = AdvanceBudgetMove.search(domain)
        if advance_move:
            budget_move.append(advance_move)
        return budget_move
