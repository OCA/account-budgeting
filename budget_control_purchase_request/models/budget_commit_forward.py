# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetCommitForward(models.Model):
    _inherit = "budget.commit.forward"

    purchase_request = fields.Boolean(
        string="Purchase Request",
        default=True,
        help="If checked, click review budget commitment will pull purchase request commitment",
    )
    forward_purchase_request_ids = fields.One2many(
        comodel_name="budget.commit.forward.line",
        inverse_name="forward_id",
        string="Purchase Request",
        domain=[("res_model", "=", "purchase.request.line")],
    )

    def _get_budget_docline_model(self):
        res = super()._get_budget_docline_model()
        if self.purchase_request:
            res.append("purchase.request.line")
        return res

    def _get_document_number(self, doc):
        if doc._name == "purchase.request.line":
            return ("{},{}".format(doc.request_id._name, doc.request_id.name),)
        return super()._get_document_number(doc)

    def _get_domain_search(self, model):
        domain_search = super()._get_domain_search(model)
        if model == "purchase.request.line":
            domain_search.extend(
                [
                    ("analytic_account_id", "!=", False),
                    ("request_state", "!=", "rejected"),
                ]
            )
        return domain_search


class BudgetCommitForwardLine(models.Model):
    _inherit = "budget.commit.forward.line"

    res_model = fields.Selection(
        selection_add=[("purchase.request.line", "Purchase Request")],
        ondelete={"purchase.request.line": "cascade"},
    )
    document_id = fields.Reference(
        selection_add=[("purchase.request.line", "Purchase Request")],
        ondelete={"purchase.request.line": "cascade"},
    )
