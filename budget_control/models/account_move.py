# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self, invoice=False):
        res = super().post(invoice=invoice)
        BudgetPeriod = self.env['budget.period']
        for doc in self:
            BudgetPeriod.check_budget(doc.line_ids)
        return res
