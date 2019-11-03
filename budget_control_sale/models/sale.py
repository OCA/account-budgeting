# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    budget_move_ids = fields.One2many(
        comodel_name='sale.budget.move',
        inverse_name='sale_id',
        string='Sales Budget Moves',
    )

    @api.multi
    def recompute_budget_move(self):
        self.mapped('order_line').recompute_budget_move()

    @api.multi
    def _write(self, vals):
        """
        - Commit budget when state changes to sale
        - Cancel/Draft document should delete all budget commitment
        """
        res = super()._write(vals)
        if vals.get('state') in ('sale', 'cancel', 'draft'):
            for sale_line in self.mapped('order_line'):
                sale_line.commit_budget()
        return res

    # No budget check on confirm Sales
    # @api.multi
    # def action_confirm(self):
    #     res = super().action_confirm()
    #     BudgetPeriod = self.env['budget.period']
    #     for doc in self:
    #         BudgetPeriod.check_budget(doc.budget_move_ids,
    #                                       doc_type='sale')
    #     return res


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'budget.docline.mixin']

    budget_move_ids = fields.One2many(
        comodel_name='sale.budget.move',
        inverse_name='sale_line_id',
        string='Sales Budget Moves',
    )

    @api.multi
    def recompute_budget_move(self):
        for sale_line in self:
            sale_line.budget_move_ids.unlink()
            # Commit on sales order
            sale_line.commit_budget()
            # Uncommitted on invoice confirm
            sale_line.invoice_lines.uncommit_sale_budget()

    @api.multi
    def commit_budget(self, product_qty=False,
                      reverse=False, invoice_line_id=False):
        """Create budget commit for each sale.order.line."""
        self.ensure_one()
        if self.state in ('sale', 'done'):
            if not product_qty:
                product_qty = self.product_uom_qty
            fpos = self.order_id.fiscal_position_id
            account = self.product_id.product_tmpl_id.\
                get_product_accounts(fpos)['income']
            company = self.env.user.company_id
            amount_currency = product_qty * self.price_unit
            date_order = self.order_id.date_order
            amount = self.currency_id._convert(
                amount_currency, company.currency_id, company, date_order)
            self.env['sale.budget.move'].create({
                'sale_line_id': self.id,
                'account_id': account.id,
                'analytic_account_id': self.order_id.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
                'date': (self._context.get('commit_by_docdate') and
                         date_order or fields.Date.today()),
                'amount_currency': amount_currency,
                'credit': not reverse and amount or 0.0,  # switch dr/cr
                'debit': reverse and amount or 0.0,
                'company_id': company.id,
                'invoice_line_id': invoice_line_id,
                })
            if reverse:  # On reverse, make sure not over returned
                self.env['budget.period'].\
                    check_over_returned_budget(self.order_id)
        else:
            self.budget_move_ids.unlink()
