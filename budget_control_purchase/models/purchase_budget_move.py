# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PurchaseBudgetMove(models.Model):
    _name = 'purchase.budget.move'
    _inherit = ['base.budget.move']
    _description = 'Purchase Budget Moves'

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
