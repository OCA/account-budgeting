# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()
        BudgetMove = self.env["advance.budget.move"]
        moves_inbound = self.filtered(lambda l: l.payment_id.payment_type == "inbound")
        # Unlink advance return commit
        if moves_inbound:
            return_advances = BudgetMove.search(
                [
                    ("move_id", "in", moves_inbound.ids),
                    ("debit", ">", 0.0),
                ]
            )
            return_advances.unlink()
        return res

    def button_draft(self):
        """Unlink return advance budget"""
        res = super().button_draft()
        BudgetMove = self.env["advance.budget.move"]
        moves_inbound = self.filtered(lambda l: l.payment_id.payment_type == "inbound")
        if moves_inbound:
            return_advances = BudgetMove.search(
                [
                    ("move_id", "in", moves_inbound.ids),
                    ("credit", ">", 0.0),
                ]
            )
            # Commit budget again
            for ret in return_advances:
                ret.expense_id.commit_budget(
                    amount_currency=ret.amount_currency,
                    move_line_id=ret.move_line_id.id,
                    date=ret.date,
                )
        return res
