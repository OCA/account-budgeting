# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        if line.get('activity_id'):
            res['activity_id'] = line['activity_id']
        return res

    @api.model
    def invoice_line_move_line_get(self):
        res = super().invoice_line_move_line_get()
        invoice_line_obj = self.env['account.invoice.line']
        for vals in res:
            if vals.get('invl_id'):
                invline = invoice_line_obj.browse(vals['invl_id'])
                if invline.activity_id:
                    vals['activity_id'] = invline.activity_id.id
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    activity_id = fields.Many2one(
        comodel_name='budget.activity',
        string='Activity',
        index=True,
    )

    @api.onchange('activity_id')
    def _onchange_activity_id(self):
        if not self.product_id:
            self.account_id = self.activity_id.account_id
