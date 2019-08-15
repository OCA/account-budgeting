# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self, invoice=False):
        res = super().post(invoice=invoice)
        BudgetManagement = self.env['budget.management']
        for doc in self:
            BudgetManagement.check_budget(doc.line_ids)
        return res
