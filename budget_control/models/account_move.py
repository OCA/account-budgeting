# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self, invoice=False):
        res = super().post(invoice=invoice)
        # Force no budget check, if not Vendor Bill
        no_check = invoice and invoice.type != 'in_invoice' and True or False
        ctx = {'force_no_budget_check': no_check}
        BudgetManagement = self.env['budget.management'].with_context(ctx)
        for doc in self:
            BudgetManagement.check_budget(doc.line_ids)
        return res
