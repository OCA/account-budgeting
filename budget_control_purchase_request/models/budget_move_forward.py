# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BudgetMoveForward(models.Model):
    _inherit = "budget.move.forward"

    forward_purchase_request_ids = fields.One2many(
        comodel_name="budget.move.forward.line",
        inverse_name="forward_id",
        string="Purchase Request",
        domain=[("res_model", "=", "purchase.request.line")],
    )

    def _get_domain_search(self, model):
        domain_search = super()._get_domain_search(model)
        if model == "purchase.request.line":
            domain_search.append(("analytic_account_id", "!=", False))
        return domain_search


class BudgetMoveForwardLine(models.Model):
    _inherit = "budget.move.forward.line"

    res_model = fields.Selection(
        selection_add=[("purchase.request.line", "Purchase Request")],
        ondelete={"purchase.request.line": "cascade"},
    )
    document_id = fields.Reference(
        selection_add=[("purchase.request.line", "Purchase Request")],
        ondelete={"purchase.request.line": "cascade"},
    )
