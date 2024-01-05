# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def write(self, vals):
        """Uncommit budget for source purchase request document."""
        res = super().write(vals)
        if vals.get("state") in ("purchase", "cancel"):
            self.mapped("order_line.purchase_request_lines").recompute_budget_move()
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def uncommit_purchase_request_budget(self):
        """For purchase in valid state, do uncommit for related PR."""
        for po_line in self:
            po_state = po_line.order_id.state
            if po_state in ("purchase", "done"):
                for pr_line in po_line.purchase_request_lines.filtered("amount_commit"):
                    analytic_account_po_line = po_line.account_analytic_id
                    analytic_account_pr_line = pr_line.analytic_account_id
                    # Set date following date commit on PO line
                    date = po_line.date_commit
                    # If Period of AA on PR line does not the same as PO line
                    # Set date as the end date of the current period
                    if (
                        analytic_account_po_line.name == analytic_account_pr_line.name
                        and analytic_account_po_line.budget_period_id
                        != analytic_account_pr_line.budget_period_id and not pr_line.fwd_analytic_account_id
                    ):
                        date = analytic_account_pr_line.bm_date_to
                    pr_line.commit_budget(
                        reverse=True,
                        purchase_line_id=po_line.id,
                        date=date,
                        analytic_account_id=pr_line.fwd_analytic_account_id or False,
                    )
            else:  # Cancel or draft, not commitment line
                self.env["purchase.request.budget.move"].search(
                    [("purchase_line_id", "=", po_line.id)]
                ).unlink()
