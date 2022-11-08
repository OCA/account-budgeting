# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def uncommit_purchase_budget(self):
        """For vendor bill in valid state, do uncommit for related purchase."""
        for ml in self:
            inv_state = ml.move_id.state
            move_type = ml.move_id.move_type
            if move_type in ("in_invoice", "in_refund"):
                if inv_state == "posted":
                    rev = move_type == "in_invoice" and True or False
                    purchase_line = ml.purchase_line_id.filtered("amount_commit")
                    if not purchase_line:
                        continue
                    qty = ml.product_uom_id._compute_quantity(
                        ml.quantity, purchase_line.product_uom
                    )
                    # Confirm vendor bill, do uncommit budget
                    qty_bf_invoice = purchase_line.qty_invoiced - qty
                    qty_balance = purchase_line.product_qty - qty_bf_invoice
                    qty = qty > qty_balance and qty_balance or qty
                    if qty <= 0:
                        continue
                    # Only case reverse and want to return_amount_commit
                    if rev and ml.return_amount_commit:
                        purchase_line = purchase_line.with_context(
                            return_amount_commit=ml.amount_commit
                        )
                    purchase_line.commit_budget(
                        reverse=rev,
                        move_line_id=ml.id,
                        analytic_account_id=ml.analytic_account_id,
                        product_qty=qty,
                        date=ml.date_commit,
                    )
                else:  # Cancel or draft, not commitment line
                    self.env["purchase.budget.move"].search(
                        [("move_line_id", "=", ml.id)]
                    ).unlink()
