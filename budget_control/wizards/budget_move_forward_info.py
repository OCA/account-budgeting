# Copyright 2021 Ecosoft - (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetMoveForwardInfo(models.TransientModel):
    _name = "budget.move.forward.info"
    _description = "Budget Move Forward Info"

    forward_id = fields.Many2one(
        comodel_name="budget.move.forward",
        index=True,
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    forward_info_line_ids = fields.One2many(
        comodel_name="budget.move.forward.info.line",
        inverse_name="forward_info_id",
        string="Forward Info Lines",
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company", related="forward_id.company_id"
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency", related="forward_id.company_currency_id"
    )

    def action_budget_carry_forward(self):
        self.ensure_one()
        forward_id = self.env["budget.move.forward"].browse(self.forward_id.id)
        forward_id.action_budget_carry_forward()


class BudgetMoveForwardInfoLine(models.TransientModel):
    _name = "budget.move.forward.info.line"
    _description = "Budget Move Forward Info Line"

    forward_info_id = fields.Many2one(
        comodel_name="budget.move.forward.info",
        index=True,
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        required=True,
    )
    analytic_group = fields.Many2one(
        comodel_name="account.analytic.group",
        string="Analytic Group",
        related="analytic_account_id.group_id",
    )
    initial_available = fields.Monetary(
        string="Initial Available",
        compute="_compute_budget_info",
        currency_field="company_currency_id",
        help="Initial Balance come from carry forward available accumulated",
    )
    initial_commit = fields.Monetary(
        string="Initial Commitment",
        compute="_compute_budget_info",
        currency_field="company_currency_id",
        help="Initial Balance from carry forward commitment",
    )
    amount_balance = fields.Monetary(
        string="Available",
        compute="_compute_budget_info",
        currency_field="company_currency_id",
        help="Available = Total Budget - Consumed",
    )
    company_id = fields.Many2one(
        comodel_name="res.company", related="forward_info_id.company_id"
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="forward_info_id.company_currency_id",
    )

    def _compute_budget_info(self):
        for rec in self:
            available_vals = rec._get_amount_from_available(
                rec.forward_info_id.forward_id
            )
            commitment_vals = rec._get_amount_from_commitment(
                rec.forward_info_id.forward_id
            )
            rec.initial_available = (
                available_vals[rec.analytic_account_id.id]["initial_available"]
                if available_vals
                and rec.analytic_account_id.id in available_vals.keys()
                else 0.0
            )
            rec.initial_commit = (
                commitment_vals[rec.analytic_account_id.id]["initial_commit"]
                if commitment_vals
                and rec.analytic_account_id.id in commitment_vals.keys()
                else 0.0
            )
            rec.amount_balance = rec.initial_available - rec.initial_commit

    def _get_amount_from_available(self, forward_id):
        available_vals = {}
        accumulate_lines = forward_id.forward_accumulate_ids
        for line in accumulate_lines:
            line._check_constraint_analytic()
            # Carry Forward
            analytic = False
            if line.method_type == "extend":
                analytic = line.analytic_account_id
            elif line.method_type == "new":
                analytic = line.to_analytic_account_id
            if analytic and analytic.id not in available_vals.keys():
                available_vals[analytic.id] = {
                    "initial_available": line.amount_carry_forward
                }
            elif analytic and analytic.id in available_vals.keys():
                initial_available = available_vals[analytic.id]["initial_available"]
                initial_available += line.amount_carry_forward
                available_vals[analytic.id].update(
                    {"initial_available": initial_available}
                )
            # Accumulate
            if (
                line.accumulate_analytic_account_id
                and line.accumulate_analytic_account_id.id not in available_vals.keys()
            ):
                available_vals[line.accumulate_analytic_account_id.id] = {
                    "initial_available": line.amount_accumulate
                }
            elif (
                line.accumulate_analytic_account_id
                and line.accumulate_analytic_account_id.id in available_vals.keys()
            ):
                initial_available = available_vals[
                    line.accumulate_analytic_account_id.id
                ]["initial_available"]
                initial_available += line.amount_accumulate
                available_vals[line.accumulate_analytic_account_id.id].update(
                    {"initial_available": initial_available}
                )
        return available_vals

    def _get_amount_from_commitment(self, forward_id):
        commitment_vals = {}
        Line = self.env["budget.move.forward.line"]
        forward_lines = Line.search([("forward_id", "=", forward_id.id)])
        for line in forward_lines:
            line._check_carry_forward_analytic()
            next_analytic = line._get_next_analytic()
            if next_analytic and next_analytic.id not in commitment_vals.keys():
                commitment_vals[next_analytic.id] = {
                    "initial_commit": line.amount_commit
                }
            elif next_analytic and next_analytic.id in commitment_vals.keys():
                commitment_vals[next_analytic.id][
                    "initial_commit"
                ] += line.amount_commit
        return commitment_vals
