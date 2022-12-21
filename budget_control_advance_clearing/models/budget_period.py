# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BudgetPeriod(models.Model):
    _inherit = "budget.period"

    advance = fields.Boolean(
        string="On Advance",
        compute="_compute_control_advance",
        store=True,
        readonly=False,
        help="Control budget on advance approved",
    )

    def _budget_info_query(self):
        query = super()._budget_info_query()
        query["info_cols"]["amount_advance"] = ("4_av_commit", True)
        return query

    @api.model
    def check_budget(self, doclines, doc_type="account"):
        if not doclines:
            return
        if doclines._name == "hr.expense":
            sheet = doclines.mapped("sheet_id")
            sheet.ensure_one()
            if sheet.advance:
                doc_type = "advance"
                doclines = doclines.with_context(
                    alt_budget_move_model="advance.budget.move",
                    alt_budget_move_field="advance_budget_move_ids",
                )
        return super().check_budget(doclines, doc_type=doc_type)

    @api.model
    def check_budget_precommit(self, doclines, doc_type="account"):
        """If the clearing has related advance, uncommit first"""
        budget_moves = False
        if doclines._name == "hr.expense":
            clearings = doclines.mapped("sheet_id").filtered("advance_sheet_id")
            budget_moves = (
                clearings.mapped("expense_line_ids")
                .with_context(force_commit=True)
                .uncommit_advance_budget()
            )
        res = super().check_budget_precommit(doclines, doc_type=doc_type)
        if budget_moves:
            budget_moves.unlink()
        return res

    @api.depends("control_budget")
    def _compute_control_advance(self):
        for rec in self:
            rec.advance = rec.control_budget

    @api.model
    def _get_eligible_budget_period(self, date=False, doc_type=False):
        budget_period = super()._get_eligible_budget_period(date, doc_type)
        # Get period control budget.
        # if doctype is advance, check special control too.
        if doc_type == "advance":
            return budget_period.filtered(
                lambda l: (l.control_budget and l.advance)
                or (not l.control_budget and l.advance)
            )
        return budget_period
