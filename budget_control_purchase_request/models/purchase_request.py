# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    budget_move_ids = fields.One2many(
        comodel_name="purchase.request.budget.move",
        inverse_name="purchase_request_id",
        string="Purchase Request Budget Moves",
    )

    def recompute_budget_move(self):
        self.mapped("line_ids").recompute_budget_move()

    def close_budget_move(self):
        self.mapped("line_ids").close_budget_move()

    def write(self, vals):
        """
        - Commit budget when state changes to approved
        - Cancel/Draft document should delete all budget commitment
        """
        res = super().write(vals)
        if vals.get("state") in ("approved", "rejected", "draft"):
            doclines = self.mapped("line_ids")
            if vals.get("state") in ("rejected", "draft"):
                doclines.write({"date_commit": False})
            doclines.recompute_budget_move()
        return res

    def button_approved(self):
        res = super().button_approved()
        self.flush()
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget(doc.line_ids, doc_type="purchase_request")
        return res

    def button_to_approve(self):
        """ Pre-Commit Check Budget """
        res = super().button_to_approve()
        self.flush()
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget_precommit(
                doc.line_ids, doc_type="purchase_request"
            )
        return res


class PurchaseRequestLine(models.Model):
    _name = "purchase.request.line"
    _inherit = ["purchase.request.line", "budget.docline.mixin"]
    _budget_date_commit_fields = ["request_id.write_date"]
    _budget_move_model = "purchase.request.budget.move"
    _doc_rel = "request_id"

    budget_move_ids = fields.One2many(
        comodel_name="purchase.request.budget.move",
        inverse_name="purchase_request_line_id",
        string="Purchase Request Budget Moves",
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        compute="_compute_account_id",
    )

    def _compute_account_id(self):
        for rec in self:
            rec.account_id = rec._get_pr_line_account()

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

    def _init_docline_budget_vals(self, budget_vals):
        self.ensure_one()
        budget_vals["amount_currency"] = self.estimated_cost
        # Document specific vals
        budget_vals.update(
            {
                "purchase_request_line_id": self.id,
                "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
            }
        )
        return super()._init_docline_budget_vals(budget_vals)

    def _valid_commit_state(self):
        states = ["approved", "done"]
        return self.request_id.state in states
