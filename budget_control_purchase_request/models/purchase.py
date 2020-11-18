# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _write(self, vals):
        """Uncommit budget for source purchase request document."""
        res = super()._write(vals)
        if vals.get("state") in ("purchase", "cancel"):
            self.mapped("order_line").uncommit_purchase_request_budget()
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def uncommit_purchase_request_budget(self):
        """For purchase in valid state, do uncommit for related PR."""
        for po_line in self:
            po_state = po_line.order_id.state
            if po_state in ("purchase", "done"):
                for pr_line in po_line.purchase_request_lines:
                    pr_line.commit_budget(reverse=True, purchase_line_id=po_line.id)
            else:  # Cancel or draft, not commitment line
                self.env["purchase.request.budget.move"].search(
                    [("purchase_line_id", "=", po_line.id)]
                ).unlink()
