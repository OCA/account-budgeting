# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _write(self, vals):
        """Uncommit budget for source purchase document."""
        res = super()._write(vals)
        if vals.get('state') in ('open', 'cancel'):
            self.mapped('invoice_line_ids').uncommit_purchase_budget()
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def uncommit_purchase_budget(self):
        """For vendor bill in valid state, do uncommit for related purchase."""
        for inv_line in self:
            inv_state = inv_line.invoice_id.state
            inv_type = inv_line.invoice_id.type
            if inv_type in ('in_invoice', 'in_refund'):
                if inv_state in ('open', 'in_payment', 'paid'):
                    rev = inv_type == 'in_invoice' and True or False
                    purchase_line = inv_line.purchase_line_id
                    if not purchase_line:
                        continue
                    qty = inv_line.uom_id._compute_quantity(
                        inv_line.quantity, purchase_line.product_uom)
                    # Confirm vendor bill, do uncommit budget)
                    qty_bf_invoice = purchase_line.qty_invoiced - qty
                    qty_balance = purchase_line.product_qty - qty_bf_invoice
                    qty = qty > qty_balance and qty_balance or qty
                    if qty <= 0:
                        continue
                    purchase_line.commit_budget(
                        qty, reverse=rev, invoice_line_id=inv_line.id)
                else:  # Cancel or draft, not commitment line
                    self.env['purchase.budget.move'].search(
                        [('invoice_line_id', '=', inv_line.id)]).unlink()
