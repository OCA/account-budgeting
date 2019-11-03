# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        # Do not check in account.move.post() if called from invoice
        self = self.with_context(force_no_budget_check=True)
        res = super().action_invoice_open()
        self = self.with_context(force_no_budget_check=False)
        BudgetPeriod = self.env['budget.period']
        # Check budget only if called from vendor bill
        invoices = self.filtered(lambda l: l.type == 'in_invoice')
        for doc in invoices.mapped('move_id'):
            BudgetPeriod.check_budget(doc.line_ids)
        return res
