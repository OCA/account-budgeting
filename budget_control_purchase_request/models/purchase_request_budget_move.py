# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PurchaseRequestBudgetMove(models.Model):
    _name = "purchase.request.budget.move"
    _inherit = ["base.budget.move"]
    _description = "Purchase Request Budget Moves"

    purchase_request_id = fields.Many2one(
        comodel_name="purchase.request",
        related="purchase_request_line_id.request_id",
        readonly=True,
        store=True,
        index=True,
    )
    purchase_request_line_id = fields.Many2one(
        comodel_name="purchase.request.line",
        readonly=True,
        index=True,
        help="Commit budget for this purchase_request_line_id",
    )
    purchase_id = fields.Many2one(
        comodel_name="purchase.order",
        related="purchase_line_id.order_id",
    )
    purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        readonly=True,
        index=True,
        help="Uncommit budget from this purchase_line_id",
    )

    @api.depends("purchase_request_id")
    def _compute_reference(self):
        for rec in self:
            rec.reference = (
                rec.reference if rec.reference else rec.purchase_request_id.display_name
            )
