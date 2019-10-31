# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleBudgetMove(models.Model):

    _name = 'sale.budget.move'
    _inherit = ['base.budget.move']
    _description = 'Sales Budget Moves'

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        related='sale_line_id.order_id',
        readonly=True,
        store=True,
        index=True,
    )
    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        readonly=True,
        index=True,
        help="Commit budget for this sale_line_id",
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
