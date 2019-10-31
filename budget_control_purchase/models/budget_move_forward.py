# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models

class BudgetMoveForward(models.Model):
    _inherit = 'budget.move.forward'

    forward_purchase_ids = fields.One2many(
        comodel_name='budget.move.forward.line',
        inverse_name='forward_id',
        string='Purchase Orders',
        domain=[('res_model', '=', 'purchase.order.line')],
    )


class BudgetMoveForwardLine(models.Model):
    _inherit = 'budget.move.forward.line'

    res_model = fields.Selection(
        selection_add=[('purchase.order.line', 'Purchase')])
    document_id = fields.Reference(
        selection_add=[('purchase.order.line', 'Purchase')])
