# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class HRExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    budget_commit_ids = fields.One2many(
        comodel_name='hr_expense.budget.commit',
        inverse_name='sheet_id',
    )

    @api.multi
    def recompute_budget_commit(self):
        self.mapped('expense_line_ids').recompute_budget_commit()

    @api.multi
    def _write(self, vals):
        """
        - Commit budget when state approved
        - Cancel/Draft document should delete all budget commitment
        """
        res = super()._write(vals)
        if vals.get('state') in ('approve', 'cancel', 'draft'):
            print(self.mapped('expense_line_ids'))
            self.mapped('expense_line_ids').commit_budget()
        elif vals.get('state') == 'post':
            self.mapped('expense_line_ids').uncommit_expense_budget()
        return res


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    budget_commit_ids = fields.One2many(
        comodel_name='hr_expense.budget.commit',
        inverse_name='expense_id',
    )

    @api.multi
    def recompute_budget_commit(self):
        self.mapped('budget_commit_ids').unlink()
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
                self.env['hr_expense.budget.commit'].create({
                    'expense_id': expense.id,
                    'account_id': expense.account_id.id,
                    'account_analytic_id': expense.analytic_account_id.id,
                    'date': expense.date,
                    'amount_currency': expense.untaxed_amount,
                    'debit': not reverse and amount or 0.0,
                    'credit': reverse and amount or 0.0,
                    'company_id': company.id,
                    })
            else:
                expense.budget_commit_ids.unlink()

    @api.multi
    def uncommit_expense_budget(self):
        """For vendor bill in valid state, do uncommit for related expense."""
        for expense in self:
            if expense.sheet_id.state in ('post', 'done') and \
                    expense.state in ('approved', 'done'):
                expense.commit_budget(reverse=True)
