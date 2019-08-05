# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    budget_commit_ids = fields.One2many(
        comodel_name='purchase.budget.commit',
        inverse_name='purchase_id',
        string='Purchase Budget Commitment',
    )

    @api.multi
    def recompute_budget_commit(self):
        self.mapped('order_line').recompute_budget_commit()

    @api.multi
    def _write(self, vals):
        """
        - Commit budget when state changes to purchase
        - Cancel/Draft document should delete all budget commitment
        """
        res = super()._write(vals)
        if vals.get('state') in ('purchase', 'cancel', 'draft'):
            for purchase_line in self.mapped('order_line'):
                purchase_line.commit_budget()
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    budget_commit_ids = fields.One2many(
        comodel_name='purchase.budget.commit',
        inverse_name='purchase_line_id',
        string='Purchase Budget Commitment',
    )

    @api.multi
    def recompute_budget_commit(self):
        for purchase_line in self:
            purchase_line.budget_commit_ids.unlink()
            # Commit on purchase order
            purchase_line.commit_budget()
            # Uncommitted on invoice confirm
            purchase_line.invoice_lines.uncommit_purchase_budget()

    @api.multi
    def commit_budget(self, product_qty=False,
                      reverse=False, invoice_line_id=False):
        """Create budget commit for each purchase.order.line."""
        self.ensure_one()
        if self.state in ('purchase', 'done'):
            if not product_qty:
                product_qty = self.product_qty
            fpos = self.order_id.fiscal_position_id
            account = self.product_id.product_tmpl_id.\
                get_product_accounts(fpos)['expense']
            company = self.env.user.company_id
            amount_currency = product_qty * self.price_unit
            date_order = self.order_id.date_order
            amount = self.currency_id._convert(
                amount_currency, company.currency_id, company, date_order)
            self.env['purchase.budget.commit'].create({
                'purchase_line_id': self.id,
                'account_id': account.id,
                'account_analytic_id': self.account_analytic_id.id,
                'date': date_order,
                'amount_currency': amount_currency,
                'debit': not reverse and amount or 0.0,
                'credit': reverse and amount or 0.0,
                'company_id': company.id,
                'invoice_line_id': invoice_line_id,
                })
        else:
            self.budget_commit_ids.unlink()
