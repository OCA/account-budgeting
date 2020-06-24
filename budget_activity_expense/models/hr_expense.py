# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class HRExpense(models.Model):
    _inherit = 'hr.expense'


class ExpenseBudgetMove(models.Model):
    _inherit = 'expense.budget.move'
