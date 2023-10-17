# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HRExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    advance_budget_move_ids = fields.One2many(
        comodel_name="advance.budget.move",
        inverse_name="sheet_id",
    )

    def write(self, vals):
        """Clearing for its Advance and Cancel payment expense"""
        doc_cancel = self.filtered(lambda l: l.state == "cancel")
        res = super().write(vals)
        if vals.get("state") in ("approve", "cancel"):
            # If this is a clearing, return commit to the advance
            advances = self.mapped("advance_sheet_id.expense_line_ids")
            if advances:
                advances.recompute_budget_move()
        # Support with module `hr_expense_cancel` if you change state cancel to post
        if vals.get("state") == "post" and doc_cancel:
            doc_cancel.mapped("expense_line_ids").recompute_budget_move()
        return res

    def _prepare_clear_advance(self, line):
        """Cleaing after carry forward Advance"""
        clearing_dict = super()._prepare_clear_advance(line)
        if clearing_dict.get("analytic_account_id") and clearing_dict.get(
            "fwd_analytic_account_id"
        ):
            clearing_dict["analytic_account_id"] = clearing_dict[
                "fwd_analytic_account_id"
            ]
            clearing_dict["date_commit"] = False
        return clearing_dict


class HRExpense(models.Model):
    _inherit = "hr.expense"

    advance_budget_move_ids = fields.One2many(
        comodel_name="advance.budget.move",
        inverse_name="expense_id",
    )

    def _filter_current_move(self, analytic):
        self.ensure_one()
        if self._context.get("advance", False):
            return self.advance_budget_move_ids.filtered(
                lambda l: l.analytic_account_id == analytic
            )
        return super()._filter_current_move(analytic)

    @api.depends("advance_budget_move_ids", "budget_move_ids")
    def _compute_commit(self):
        advances = self.filtered("advance")
        expenses = self - advances
        # Advances
        for rec in advances:
            debit = sum(rec.advance_budget_move_ids.mapped("debit"))
            credit = sum(rec.advance_budget_move_ids.mapped("credit"))
            rec.amount_commit = debit - credit
            if rec.advance_budget_move_ids:
                rec.date_commit = min(rec.advance_budget_move_ids.mapped("date"))
            else:
                rec.date_commit = False
        # Expenses
        return super(HRExpense, expenses)._compute_commit()

    def _get_account_move_by_sheet(self):
        # When advance create move, do set not_affect_budget = True
        move_grouped_by_sheet = super()._get_account_move_by_sheet()
        for sheet in self.mapped("sheet_id").filtered("advance"):
            move_grouped_by_sheet[sheet.id].not_affect_budget = True
        return move_grouped_by_sheet

    def _find_next_av(self, advance):
        next_av = self.filtered(
            lambda l: l.advance
            and l.id != advance.id
            and l.amount_commit
            and l.sheet_id == advance.sheet_id
        )
        return next_av[0] if next_av else advance

    def _get_recompute_advances(self):
        advances = self.filtered(lambda l: l.advance)
        res = False
        if advances:
            # date_commit return list, so we check in list again
            if advances.mapped("date_commit") and advances.mapped("date_commit")[0]:
                advance_date_commit = advances.mapped("date_commit")[0]
            else:
                advance_date_commit = self.env.context.get("force_date_commit", False)
            res = super(
                HRExpense,
                advances.with_context(
                    alt_budget_move_model="advance.budget.move",
                    alt_budget_move_field="advance_budget_move_ids",
                    force_date_commit=advance_date_commit,
                ),
            ).recompute_budget_move()
            advance_sheet = advances.mapped("sheet_id")
            advance_sheet.ensure_one()
            # If the advances has any clearing, uncommit them from advance
            clearings = self.search(
                [("sheet_id.advance_sheet_id", "=", advance_sheet.id)]
            )
            clearings.uncommit_advance_budget()
            # If the advances has any reconcile (return advance),
            # reverse commit them from advance
            aml_debit = advance_sheet.account_move_id.line_ids.filtered(
                lambda l: l.debit
            )
            ml_reconcile = aml_debit.matched_credit_ids
            for reconcile in ml_reconcile:
                # Debit side (Advance)
                advance = reconcile.debit_move_id.expense_id
                amount_return = reconcile.debit_amount_currency
                # Credit side (Return Advance)
                return_ml = reconcile.credit_move_id
                if advance:
                    advance.commit_budget(
                        reverse=True,
                        amount_currency=amount_return,
                        move_line_id=return_ml.id,
                        date=return_ml.date_commit,
                    )
        return res

    def _close_budget_sheets_with_adj_commit(self):
        advance_budget_moves = self.filtered("advance_budget_move_ids.adj_commit")
        for sheet in advance_budget_moves.mapped("sheet_id"):
            # And only if some adjustment has occured
            adj_moves = sheet.advance_budget_move_ids.filtered("adj_commit")
            moves = sheet.advance_budget_move_ids - adj_moves
            # If adjust > over returned
            adjusted = sum(adj_moves.mapped("debit"))
            over_returned = sum(moves.mapped(lambda l: l.credit - l.debit))
            if adjusted > over_returned:
                sheet.close_budget_move()

    def recompute_budget_move(self):
        if not self:
            return
        # Recompute budget moves for expenses
        expenses = self.filtered(lambda l: not l.advance)
        res = super(HRExpense, expenses).recompute_budget_move()
        # Recompute budget moves for advances
        self._get_recompute_advances()
        # Return advance, commit again because it will lose from clearing uncommit
        # Only when advance is over returned, do close_budget_move() to final adjust
        # Note: now, we only found case in Advance / Return / Clearing case
        self._close_budget_sheets_with_adj_commit()
        return res

    def close_budget_move(self):
        # Expenses
        expenses = self.filtered(lambda l: not l.advance)
        super(HRExpense, expenses).close_budget_move()
        # Advances)
        advances = self.filtered(lambda l: l.advance).with_context(
            alt_budget_move_model="advance.budget.move",
            alt_budget_move_field="advance_budget_move_ids",
        )
        return super(HRExpense, advances).close_budget_move()

    def commit_budget(self, reverse=False, **vals):
        if self.advance:
            self = self.with_context(
                alt_budget_move_model="advance.budget.move",
                alt_budget_move_field="advance_budget_move_ids",
            )
        return super().commit_budget(reverse=reverse, **vals)

    def uncommit_advance_budget(self):
        """For clearing in valid state,
        do uncommit for related Advance sorted by date commit."""
        budget_moves = self.env["advance.budget.move"]
        # Sorted clearing by date_commit first. for case clearing > advance
        # it should uncommit clearing that approved first
        clearing_approved = self.filtered("date_commit")
        clearing_not_approved = self - clearing_approved
        clearing_sorted = (
            clearing_approved.sorted(key=lambda l: l.date_commit)
            + clearing_not_approved
        )
        for clearing in clearing_sorted:
            cl_state = clearing.sheet_id.state
            if self.env.context.get("force_commit") or cl_state in (
                "approve",
                "post",  # clearing more than advance, it change to state post
                "done",
            ):
                # With possibility to have multiple advance lines,
                # just return amount line by line
                origin_clearing_amount = (
                    clearing.total_amount
                    if self.env.company.budget_include_tax
                    else clearing.untaxed_amount
                )
                while origin_clearing_amount > 0:
                    advance_sheet = clearing.sheet_id.advance_sheet_id
                    advances = advance_sheet.expense_line_ids.filtered("amount_commit")
                    if not advances:
                        break
                    for advance in advances:
                        clearing_amount = min(
                            advance.amount_commit, origin_clearing_amount
                        )
                        origin_clearing_amount -= clearing_amount
                        budget_move = advance.commit_budget(
                            reverse=True,
                            clearing_id=clearing.id,
                            amount_currency=clearing_amount,
                            analytic_account_id=advance.fwd_analytic_account_id
                            or False,
                            date=clearing.date_commit,
                        )
                        budget_moves |= budget_move
                        if origin_clearing_amount <= 0:
                            break
            else:
                # Cancel or draft, not commitment line
                self.env["advance.budget.move"].search(
                    [("clearing_id", "=", clearing.id)]
                ).unlink()
        return budget_moves
