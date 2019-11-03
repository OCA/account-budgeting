# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    budget_move_ids = fields.One2many(
        comodel_name='purchase.request.budget.move',
        inverse_name='purchase_request_id',
        string='Purchase Request Budget Moves',
    )

    @api.multi
    def recompute_budget_move(self):
        self.mapped('line_ids').recompute_budget_move()

    @api.multi
    def _write(self, vals):
        """
        - Commit budget when state changes to approved
        - Cancel/Draft document should delete all budget commitment
        """
        res = super()._write(vals)
        if vals.get('state') in ('approved', 'rejected', 'draft'):
            for pr_line in self.mapped('line_ids'):
                pr_line.commit_budget()
        return res

    @api.multi
    def button_approved(self):
        res = super().button_approved()
        BudgetPeriod = self.env['budget.period']
        for doc in self:
            BudgetPeriod.check_budget(doc.budget_move_ids,
                                      doc_type='purchase_request')
        return res


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _inherit = ['purchase.request.line', 'budget.docline.mixin']

    budget_move_ids = fields.One2many(
        comodel_name='purchase.request.budget.move',
        inverse_name='purchase_request_line_id',
        string='Purchase Request Budget Moves',
    )

    @api.multi
    def recompute_budget_move(self):
        for pr_line in self:
            pr_line.budget_move_ids.unlink()
            # Commit on purchase request
            pr_line.commit_budget()
            # Uncommitted on purchase confirm
            pr_line.purchase_lines.uncommit_purchase_request_budget()

    @api.multi
    def commit_budget(self, reverse=False, purchase_line_id=False):
        """Create budget commit for each purchase.request.line."""
        self.ensure_one()
        if self.request_id.state in ('approved', 'done'):
            account = self.product_id.product_tmpl_id.\
                get_product_accounts()['expense']
            company = self.env.user.company_id
            # Purchase request has no currency to _convert()
            amount_currency = amount = self.estimated_cost
            date_start = self.request_id.date_start
            self.env['purchase.request.budget.move'].create({
                'purchase_request_line_id': self.id,
                'account_id': account.id,
                'analytic_account_id': self.analytic_account_id.id,
                'date': (self._context.get('commit_by_docdate') and
                         date_start or fields.Date.today()),
                'amount_currency': amount_currency,
                'debit': not reverse and amount or 0.0,
                'credit': reverse and amount or 0.0,
                'company_id': company.id,
                'purchase_line_id': purchase_line_id,
                })
            if reverse:  # On reverse, make sure not over returned
                self.env['budget.period'].\
                    check_over_returned_budget(self.request_id)
        else:
            self.budget_move_ids.unlink()
