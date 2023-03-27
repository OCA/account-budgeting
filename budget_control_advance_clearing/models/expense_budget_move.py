# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ExpenseBudgetMove(models.Model):
    _inherit = "expense.budget.move"

    @api.depends("sheet_id")
    def _compute_source_document(self):
        res = super()._compute_source_document()
        for rec in self.filtered("sheet_id.advance_sheet_id"):
            if hasattr(rec.sheet_id.advance_sheet_id, "number"):
                display_name = rec.sheet_id.advance_sheet_id.number
            else:
                display_name = rec.sheet_id.advance_sheet_id.display_name
            rec.source_document = rec.source_document or display_name
        return res
