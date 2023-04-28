# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_po_line_amount_commit(self):
        """For hook, addition filter or condition i.e. purchase deposit"""
        self.ensure_one()
        return self.purchase_line_id.filtered("amount_commit")

    def _check_skip_negative_qty(self):
        """For hook, addition filter or condition i.e. purchase deposit"""
        self.ensure_one()
        return self.env.context.get("skip_negative_qty", False)

    def _get_qty_commit(self, purchase_line):
        """For hook, addition filter or condition i.e. purchase deposit"""
        qty = self.product_uom_id._compute_quantity(
            self.quantity, purchase_line.product_uom
        )
        qty_bf_invoice = purchase_line.qty_invoiced - qty
        qty_balance = purchase_line.product_qty - qty_bf_invoice
        qty = min(qty, qty_balance)
        return qty

    def uncommit_purchase_budget(self):
        """For vendor bill in valid state, do uncommit for related purchase."""
        for ml in self.filtered(
            lambda l: l.move_id.move_type in ("in_invoice", "in_refund")
        ):
            inv_state = ml.move_id.state
            move_type = ml.move_id.move_type
            # Cancel or draft, not commitment line
            if inv_state != "posted":
                self.env["purchase.budget.move"].search(
                    [("move_line_id", "=", ml.id)]
                ).unlink()
                continue
            # Vendor bills and purchase order must be related and po must commit budget already
            purchase_line = ml._get_po_line_amount_commit()
            if not purchase_line:
                continue
            # Vendor bills must be qty > 0
            qty = ml._get_qty_commit(purchase_line)
            if qty <= 0 and not ml._check_skip_negative_qty():
                continue
            # Only case reverse and want to return_amount_commit
            context = {}
            if move_type == "in_invoice" and ml.return_amount_commit:
                context["return_amount_commit"] = ml.amount_commit
            # Confirm vendor bill, do uncommit budget
            purchase_line.with_context(**context).commit_budget(
                reverse=move_type == "in_invoice",
                move_line_id=ml.id,
                analytic_account_id=ml.analytic_account_id,
                product_qty=qty,
                date=ml.date_commit,
            )
