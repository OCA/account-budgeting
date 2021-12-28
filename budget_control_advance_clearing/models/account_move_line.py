# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _hook_advance_extension(self, expense):
        self.ensure_one()
        res = super()._hook_advance_extension(expense)
        ParcialReconcile = self.env["account.partial.reconcile"]
        # Return Advance should uncommit
        reconciles = ParcialReconcile.search([("debit_move_id", "=", self.id)])
        for reconcile in reconciles:
            expense.commit_budget(
                reverse=True,
                amount_currency=reconcile.debit_amount_currency,
                move_line_id=reconcile.id,
            )
        return res

    def remove_move_reconcile(self):
        """Trigger recompute budget move on Advance,
        User can reset to draft payment return advance and
        it should be compute budget again.
        """
        expense_id = self.matched_debit_ids.debit_move_id.expense_id
        res = super().remove_move_reconcile()
        expense_id.sheet_id.recompute_budget_move()
        return res
