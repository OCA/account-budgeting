# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def button_draft(self):
        """ Unlink return advance budget """
        res = super().button_draft()
        payment = self.payment_id
        if payment and payment.payment_type == "inbound":
            budget_moves = self.env["advance.budget.move"]
            return_advances = budget_moves.search([("move_id", "=", self.id)])
            return_advances.unlink()
        return res
