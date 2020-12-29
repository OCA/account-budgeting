# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    budget_move_ids = fields.One2many(
        comodel_name="purchase.request.budget.move",
        inverse_name="purchase_request_id",
        string="Purchase Request Budget Moves",
    )

    def recompute_budget_move(self):
        self.mapped("line_ids").recompute_budget_move()

    def _write(self, vals):
        """
        - Commit budget when state changes to To be approved
        - Cancel/Draft document should delete all budget commitment
        """
        res = super()._write(vals)
        if vals.get("state") in ("to_approve", "rejected", "draft"):
            BudgetControl = self.env["budget.control"]
            pr_lines = self.mapped("line_ids")
            analytic_account_ids = pr_lines.mapped("analytic_account_id")
            budget_control = BudgetControl.search(
                [("analytic_account_id", "in", analytic_account_ids.ids)]
            )
            if any(state != "done" for state in budget_control.mapped("state")):
                raise UserError(_("Analytic Account is not Controlled"))
            for pr_line in pr_lines:
                pr_line.commit_budget()
        return res

    def button_to_approve(self):
        res = super().button_to_approve()
        self.flush()
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget(doc.budget_move_ids, doc_type="purchase_request")
        return res


class PurchaseRequestLine(models.Model):
    _name = "purchase.request.line"
    _inherit = ["purchase.request.line", "budget.docline.mixin"]

    budget_move_ids = fields.One2many(
        comodel_name="purchase.request.budget.move",
        inverse_name="purchase_request_line_id",
        string="Purchase Request Budget Moves",
    )

    def recompute_budget_move(self):
        for pr_line in self:
            pr_line.budget_move_ids.unlink()
            # Commit on purchase request
            pr_line.commit_budget()
            # Uncommitted on purchase confirm
            pr_line.purchase_lines.uncommit_purchase_request_budget()

    def _get_pr_line_account(self):
        account = self.product_id.product_tmpl_id.get_product_accounts()["expense"]
        return account

    def commit_budget(self, reverse=False, purchase_line_id=False):
        """Create budget commit for each purchase.request.line."""
        self.ensure_one()
        if self.request_id.state in ("to_approve", "done"):
            account = self._get_pr_line_account()
            analytic_account = self.analytic_account_id
            doc_date = self.request_id.date_start
            amount_currency = self.estimated_cost
            currency = False  # no currency, amount = amount_currency
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
                    "purchase_request_line_id": self.id,
                    "purchase_line_id": purchase_line_id,
                }
            )
            self.env["purchase.request.budget.move"].create(vals)
            if reverse:  # On reverse, make sure not over returned
                self.env["budget.period"].check_over_returned_budget(self.request_id)
        else:
            self.budget_move_ids.unlink()
