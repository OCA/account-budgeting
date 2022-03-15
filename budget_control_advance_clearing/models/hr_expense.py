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
        """ Clearing for its Advance """
        res = super().write(vals)
        if vals.get("state") in ("approve", "cancel"):
            # If this is a clearing, return commit to the advance
            advances = self.mapped("advance_sheet_id.expense_line_ids")
            if advances:
                advances.recompute_budget_move()
        return res


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
        for rec in self:
            debit = sum(rec.advance_budget_move_ids.mapped("debit"))
            credit = sum(rec.advance_budget_move_ids.mapped("credit"))
            rec.amount_commit = debit - credit
            if rec.advance_budget_move_ids:
                rec.date_commit = min(rec.advance_budget_move_ids.mapped("date"))
            else:
                rec.date_commit = False
        # Expenses
        super(HRExpense, expenses)._compute_commit()

    def _get_account_move_by_sheet(self):
        # When advance create move, do set not_affect_budget = True
        move_grouped_by_sheet = super()._get_account_move_by_sheet()
        for sheet in self.mapped("sheet_id").filtered("advance"):
            move_grouped_by_sheet[sheet.id].not_affect_budget = True
        return move_grouped_by_sheet

    def recompute_budget_move(self):
        # Keep value return advance (Not include case carry commitment)
        budget_moves = self.env["advance.budget.move"]
        return_budget_moves = []
        if self._context.get("model") != "budget.commit.forward":
            return_advances = budget_moves.search(
                [("sheet_id", "=", self.sheet_id.id), ("move_line_id", "!=", False)]
            )
            return_budget_moves = [
                (x.move_line_id, x.amount_currency, x.expense_id)
                for x in return_advances
            ]
        # Expenses
        expenses = self.filtered(lambda l: not l.advance)
        super(HRExpense, expenses).recompute_budget_move()
        # Advances
        advances = self.filtered(lambda l: l.advance).with_context(
            alt_budget_move_model="advance.budget.move",
            alt_budget_move_field="advance_budget_move_ids",
        )
        super(HRExpense, advances).recompute_budget_move()
        # If the advances has any clearing, uncommit them from advance
        adv_sheets = advances.mapped("sheet_id")
        clearings = self.search([("sheet_id.advance_sheet_id", "in", adv_sheets.ids)])
        clearings.uncommit_advance_budget()
        # Return advance, commit again because it will lose from clearing uncommit
        for move_line, amount, expense in return_budget_moves:
            expense.commit_budget(
                reverse=True, amount_currency=amount, move_line_id=move_line.id
            )
        # Only when advance is over returned, do close_budget_move() to final adjust
        # Note: now, we only found case in Advance / Return / Clearing case
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

    def close_budget_move(self):
        # Expenses
        expenses = self.filtered(lambda l: not l.advance)
        super(HRExpense, expenses).close_budget_move()
        # Advances)
        advances = self.filtered(lambda l: l.advance).with_context(
            alt_budget_move_model="advance.budget.move",
            alt_budget_move_field="advance_budget_move_ids",
        )
        super(HRExpense, advances).close_budget_move()

    def commit_budget(self, reverse=False, **vals):
        if self.advance:
            self = self.with_context(
                alt_budget_move_model="advance.budget.move",
                alt_budget_move_field="advance_budget_move_ids",
            )
        return super().commit_budget(reverse=reverse, **vals)

    def uncommit_advance_budget(self):
        """For clearing in valid state, do uncommit for related Advance."""
        budget_moves = self.env["advance.budget.move"]
        for clearing in self:
            cl_state = clearing.sheet_id.state
            if self.env.context.get("force_commit") or cl_state in (
                "approve",
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
                        clearing_amount = (
                            advance.amount_commit
                            if advance.amount_commit < origin_clearing_amount
                            else origin_clearing_amount
                        )
                        origin_clearing_amount -= clearing_amount
                        budget_move = advance.commit_budget(
                            reverse=True,
                            clearing_id=clearing.id,
                            amount_currency=clearing_amount,
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
