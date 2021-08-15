# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetControl(models.Model):
    _inherit = "budget.control"

    amount_purchase_request = fields.Monetary(
        string="Purchase Request",
        compute="_compute_budget_info",
        help="Sum of purchase amount",
    )

    def get_move_commit(self, domain):
        budget_move = super().get_move_commit(domain)
        PurchaseRequestBudgetMove = self.env["purchase.request.budget.move"]
        pr_move = PurchaseRequestBudgetMove.search(domain)
        if pr_move:
            budget_move.append(pr_move)
        return budget_move
