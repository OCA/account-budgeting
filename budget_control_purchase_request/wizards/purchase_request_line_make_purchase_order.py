# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    def make_purchase_order(self):
        res = super().make_purchase_order()
        if res.get("domain"):
            purchase_id = res.get("domain")[0][2]
            purchase = self.env["purchase.order"].browse(purchase_id)
            if purchase.state in ("purchase", "done"):
                purchase.recompute_budget_move()
                requests = self.item_ids.mapped("line_id.request_id")
                requests.recompute_budget_move()
        return res
