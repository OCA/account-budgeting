# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetCommitForward(models.Model):
    _inherit = "budget.commit.forward"

    purchase_request = fields.Boolean(
        default=True,
        help="If checked, click review budget commitment will pull purchase request commitment",
    )
    forward_purchase_request_ids = fields.One2many(
        comodel_name="budget.commit.forward.line",
        inverse_name="forward_id",
        string="Purchase Requests",
        domain=[("res_model", "=", "purchase.request.line")],
    )

    def _get_budget_docline_model(self):
        res = super()._get_budget_docline_model()
        if self.purchase_request:
            res.append("purchase.request.line")
        return res

    def _get_document_number(self, doc):
        if doc._name == "purchase.request.line":
            return f"{doc.request_id._name},{doc.request_id.id}"
        return super()._get_document_number(doc)

    def _get_commit_docline(self, res_model):
        if res_model == "purchase.request.line":
            domain = self._get_base_domain()
            domain.extend(
                [
                    ("analytic_account_id", "!=", False),
                    ("request_state", "!=", "rejected"),
                ]
            )
            return self.env[res_model].search(domain)
        return super()._get_commit_docline(res_model)


class BudgetCommitForwardLine(models.Model):
    _inherit = "budget.commit.forward.line"

    res_model = fields.Selection(
        selection_add=[("purchase.request.line", "Purchase Request Line")],
        ondelete={"purchase.request.line": "cascade"},
    )
    document_id = fields.Reference(
        selection_add=[("purchase.request.line", "Purchase Request Line")],
        ondelete={"purchase.request.line": "cascade"},
    )
    document_number = fields.Reference(
        selection_add=[("purchase.request", "Purchase Request")],
        ondelete={"purchase.request": "cascade"},
    )
