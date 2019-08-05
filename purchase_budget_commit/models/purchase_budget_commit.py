# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PurchaseBudgetCommit(models.Model):

    _name = 'purchase.budget.commit'
    _description = 'Purchase Budget Commitment'

    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        related='purchase_line_id.order_id',
        readonly=True,
        store=True,
        index=True,
    )
    purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        readonly=True,
        index=True,
        help="Commit budget for this purchase_line_id",
    )
    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        related='invoice_line_id.invoice_id',
    )
    invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        readonly=True,
        index=True,
        help="Uncommit budget from this invoice_line_id",
    )
    date = fields.Date(
        required=True,
        index=True,
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        auto_join=True,
        index=True,
        readonly=True,
    )
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
        auto_join=True,
        index=True,
        readonly=True,
    )
    amount_currency = fields.Float(
        required=True,
        help="Amount in multi currency",
    )
    credit = fields.Float(
        readonly=True,
    )
    debit = fields.Float(
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id,
        index=True,
    )
