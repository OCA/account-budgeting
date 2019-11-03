# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class HRExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    budget_move_ids = fields.One2many(
        comodel_name='expense.budget.move',
        inverse_name='sheet_id',
    )

    @api.multi
    def recompute_budget_move(self):
        self.mapped('expense_line_ids').recompute_budget_move()

    @api.multi
    def _write(self, vals):
        """
        - Commit budget when state approved
        - Cancel/Draft document should delete all budget commitment
        """
        res = super()._write(vals)
        if vals.get('state') in ('approve', 'cancel', 'draft'):
            self.mapped('expense_line_ids').commit_budget()
        elif vals.get('state') == 'post':
            self.mapped('expense_line_ids').uncommit_expense_budget()
        return res

    @api.multi
    def approve_expense_sheets(self):
        res = super().approve_expense_sheets()
        BudgetPeriod = self.env['budget.period']
        for doc in self:
            BudgetPeriod.check_budget(doc.budget_move_ids,
                                          doc_type='expense')
        return res


class HRExpense(models.Model):
    _name = 'hr.expense'
    _inherit = ['hr.expense', 'budget.docline.mixin']

    budget_move_ids = fields.One2many(
        comodel_name='expense.budget.move',
        inverse_name='expense_id',
    )

    @api.multi
    def recompute_budget_move(self):
        self.mapped('budget_move_ids').unlink()
        self.commit_budget()
        self.uncommit_expense_budget()

    @api.multi
    def commit_budget(self, reverse=False):
        """Create budget commit for each expense."""
        for expense in self:
            if expense.state in ('approved', 'done'):
                company = self.env.user.company_id
                amount = expense.currency_id._convert(
                    expense.untaxed_amount, company.currency_id,
                    company, expense.date)
                self.env['expense.budget.move'].create({
                    'expense_id': expense.id,
                    'account_id': expense.account_id.id,
                    'analytic_account_id': expense.analytic_account_id.id,
                    'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                    'date': (self._context.get('commit_by_docdate') and
                             expense.date or fields.Date.today()),
                    'amount_currency': expense.untaxed_amount,
                    'debit': not reverse and amount or 0.0,
                    'credit': reverse and amount or 0.0,
                    'company_id': company.id,
                    })
                if reverse:  # On reverse, make sure not over returned
                    self.env['budget.period'].\
                        check_over_returned_budget(self.sheet_id)
            else:
                expense.budget_move_ids.unlink()

    @api.multi
    def uncommit_expense_budget(self):
        """For vendor bill in valid state, do uncommit for related expense."""
        for expense in self:
            if expense.sheet_id.state in ('post', 'done') and \
                    expense.state in ('approved', 'done'):
                expense.commit_budget(reverse=True)
