# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetControl(models.Model):
    _inherit = "budget.control"

    amount_purchase = fields.Monetary(
        string="Purchase",
        compute="_compute_budget_info",
        help="Sum of purchase amount",
    )

    def get_move_commit(self, domain):
        budget_move = super().get_move_commit(domain)
        PurchaseBudgetMove = self.env["purchase.budget.move"]
        purchase_move = PurchaseBudgetMove.search(domain)
        if purchase_move:
            budget_move.append(purchase_move)
        return budget_move
