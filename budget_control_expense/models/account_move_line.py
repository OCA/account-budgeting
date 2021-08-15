# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def uncommit_expense_budget(self):
        """For vendor bill in valid state, do uncommit for related expense."""
        Expense = self.env["hr.expense"]
        for ml in self.filtered("can_commit"):
            inv_state = ml.move_id.state
            move_type = ml.move_id.move_type
            if move_type in ("entry"):
                if inv_state == "posted":
                    expense = ml.expense_id
                    # Because this is not invoice, we need to compare account
                    if not expense or ml.account_id != expense.account_id:
                        continue
                    expense.with_context(uncommit=True).commit_budget(
                        reverse=True, move_line_id=ml.id
                    )
                else:  # Cancel or draft, not commitment line
                    self.env[Expense._budget_model()].search(
                        [("move_line_id", "=", ml.id)]
                    ).unlink()
