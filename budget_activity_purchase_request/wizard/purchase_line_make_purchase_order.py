# Copyright 2018-2019 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    @api.model
    def _prepare_purchase_order_line(self, po, item):
        vals = super()._prepare_purchase_order_line(po, item)
        vals["activity_id"] = item.activity_id.id
        return vals

    @api.model
    def _prepare_item(self, line):
        vals = super()._prepare_item(line)
        vals["activity_id"] = line.activity_id.id
        return vals

    @api.model
    def _get_order_line_search_domain(self, order, item):
        order_line_data = super()._get_order_line_search_domain(order, item)
        order_line_data.append(("activity_id", "=", item.activity_id.id))
        return order_line_data


class PurchaseRequestLineMakePurchaseOrderItem(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order.item"

    activity_id = fields.Many2one(
        comodel_name="budget.activity",
        string="Activity",
        readonly=False,
    )
