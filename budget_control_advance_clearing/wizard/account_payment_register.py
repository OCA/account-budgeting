# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def expense_post_return_advance(self):
        """Use reconciled data to return advance budget commit"""
        res = super().expense_post_return_advance()
        reconciles = res.get("partials")
        if not reconciles:
            return res
        # Return advance (debit side)
        for reconcile in reconciles:
            advance = reconcile.debit_move_id.expense_id
            amount_return = reconcile.debit_amount_currency
            payment_move_line_id = reconcile.credit_move_id
            advance.commit_budget(
                reverse=True,
                amount_currency=amount_return,
                move_line_id=payment_move_line_id.id,
            )
        return res
