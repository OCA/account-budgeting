# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    budget_move_ids = fields.One2many(
        comodel_name="purchase.budget.move",
        inverse_name="purchase_id",
        string="Purchase Budget Moves",
    )

    def recompute_budget_move(self):
        self.mapped("order_line").recompute_budget_move()

    def _write(self, vals):
        """
        - Commit budget when state changes to purchase
        - Cancel/Draft document should delete all budget commitment
        """
        res = super()._write(vals)
        if vals.get("state") in ("purchase", "cancel", "draft"):
            BudgetControl = self.env["budget.control"]
            purchase_line = self.mapped("order_line")
            analytic_account_ids = purchase_line.mapped("account_analytic_id")
            budget_control = BudgetControl.search(
                [("analytic_account_id", "in", analytic_account_ids.ids)]
            )
            if any(state != "done" for state in budget_control.mapped("state")):
                raise UserError(_("Analytic Account is not Controlled"))
            for purchase_line in self.mapped("order_line"):
                purchase_line.commit_budget()
        return res

    def button_confirm(self):
        res = super().button_confirm()
        self.flush()
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget(doc.budget_move_ids, doc_type="purchase")
        return res


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "budget.docline.mixin"]

    budget_move_ids = fields.One2many(
        comodel_name="purchase.budget.move",
        inverse_name="purchase_line_id",
        string="Purchase Budget Moves",
    )

    def recompute_budget_move(self):
        for purchase_line in self:
            purchase_line.budget_move_ids.unlink()
            # Commit on purchase order
            purchase_line.commit_budget()
            # Uncommitted on invoice confirm
            purchase_line.invoice_lines.uncommit_purchase_budget()

    def _get_po_line_account(self):
        fpos = self.order_id.fiscal_position_id
        account = self.product_id.product_tmpl_id.get_product_accounts(fpos)["expense"]
        return account

    def _check_amount_currency_tax(self, product_qty, date, doc_type="purchase"):
        self.ensure_one()
        budget_period = self.env["budget.period"]._get_eligible_budget_period(
            date, doc_type
        )
        amount_currency = product_qty * self.price_unit
        if budget_period.include_tax:
            amount_currency += product_qty * self.price_tax / self.product_qty
        return amount_currency

    def commit_budget(self, product_qty=False, reverse=False, move_line_id=False):
        """Create budget commit for each purchase.order.line."""
        self.ensure_one()
        if self.state in ("purchase", "done"):
            if not product_qty:
                product_qty = self.product_qty
            account = self._get_po_line_account()
            analytic_account = self.account_analytic_id
            doc_date = self.order_id.date_order
            amount_currency = self._check_amount_currency_tax(product_qty, doc_date)
            currency = self.currency_id
            vals = self._prepare_budget_commitment(
                account,
                analytic_account,
                doc_date,
                amount_currency,
                currency,
                reverse=reverse,
            )
            # Document specific vals
            vals.update(
                {
                    "purchase_line_id": self.id,
                    "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
                    "move_line_id": move_line_id,
                }
            )
            self.env["purchase.budget.move"].create(vals)
            if reverse:  # On reverse, make sure not over returned
                self.env["budget.period"].check_over_returned_budget(self.order_id)
        else:
            self.budget_move_ids.unlink()
