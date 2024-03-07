# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _init_payments(self, to_process, edit_mode=False):
        """Make sure that move in payment must not affect budget"""
        payments = super()._init_payments(to_process, edit_mode)
        payments.mapped("move_id").write({"not_affect_budget": True})
        return payments
