# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseBudgetMove(models.Model):
    _inherit = "purchase.budget.move"

    @api.depends("purchase_id")
    def _compute_source_document(self):
        res = super()._compute_source_document()
        for rec in self.filtered(lambda l: l.purchase_line_id.purchase_request_lines):
            rec.source_document = (
                rec.source_document
                if rec.source_document
                else ", ".join(
                    rec.purchase_line_id.purchase_request_lines.mapped(
                        "request_id.name"
                    )
                )
            )
        return res
