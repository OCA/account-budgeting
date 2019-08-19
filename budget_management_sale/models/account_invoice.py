# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _write(self, vals):
        """Uncommit budget for source sale document."""
        res = super()._write(vals)
        if vals.get('state') in ('open', 'cancel'):
            self.mapped('invoice_line_ids').uncommit_sale_budget()
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def uncommit_sale_budget(self):
        """For cust invoice in valid state, do uncommit for related sale."""
        for inv_line in self:
            inv_state = inv_line.invoice_id.state
            inv_type = inv_line.invoice_id.type
            if inv_type in ('out_invoice', 'out_refund'):
                if inv_state in ('open', 'in_payment', 'paid'):
                    rev = inv_type == 'out_invoice' and True or False
                    sale_line = inv_line.sale_line_ids
                    if not sale_line:
                        continue
                    sale_line.ensure_one()  # Not implement for merged line yet
                    qty = inv_line.uom_id._compute_quantity(
                        inv_line.quantity, sale_line.product_uom)
                    # Confirm customer invoice, do uncommit budget)
                    qty_balance = sale_line.product_uom_qty - \
                        sale_line.qty_to_invoice
                    qty = qty > qty_balance and qty_balance or qty
                    if qty <= 0:
                        continue
                    sale_line.commit_budget(
                        qty, reverse=rev, invoice_line_id=inv_line.id)
                else:  # Cancel or draft, not commitment line
                    self.env['sale.budget.move'].search(
                        [('invoice_line_id', '=', inv_line.id)]).unlink()
