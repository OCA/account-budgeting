# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PurchaseBudgetMove(models.Model):
    _name = "purchase.budget.move"
    _inherit = ["base.budget.move"]
    _description = "Purchase Budget Moves"

    purchase_id = fields.Many2one(
        comodel_name="purchase.order",
        related="purchase_line_id.order_id",
        readonly=True,
        store=True,
        index=True,
    )
    purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        readonly=True,
        index=True,
        help="Commit budget for this purchase_line_id",
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        related="move_line_id.move_id",
        store=True,
    )
    move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        readonly=True,
        index=True,
        help="Uncommit budget from this move_line_id",
    )

    @api.depends("purchase_id")
    def _compute_reference(self):
        for rec in self:
            rec.reference = (
                rec.reference if rec.reference else rec.purchase_id.display_name
            )
