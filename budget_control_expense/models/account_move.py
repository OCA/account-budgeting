# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        """Uncommit budget for source expense document."""
        res = super().write(vals)
        if vals.get("state") in ("draft", "posted", "cancel"):
            self.mapped("line_ids.expense_id").recompute_budget_move()
        return res
