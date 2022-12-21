# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def button_draft(self):
        """Unlink return advance budget"""
        res = super().button_draft()
        BudgetMove = self.env["advance.budget.move"]
        moves_inbound = self.filtered(lambda l: l.payment_id.payment_type == "inbound")
        if moves_inbound:
            return_advances = BudgetMove.search([("move_id", "in", moves_inbound.ids)])
            return_advances.unlink()
        return res
