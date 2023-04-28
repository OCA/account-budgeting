# Copyright 2021 Ecosoft - (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BudgetBalanceForwardInfo(models.TransientModel):
    _name = "budget.balance.forward.info"
    _description = "Budget Balance Forward Info"

    forward_id = fields.Many2one(
        comodel_name="budget.balance.forward",
        index=True,
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    forward_info_line_ids = fields.One2many(
        comodel_name="budget.balance.forward.info.line",
        inverse_name="forward_info_id",
        string="Forward Info Lines",
        readonly=True,
    )
    currency_id = fields.Many2one(
        related="forward_id.currency_id",
    )

    def action_budget_balance_forward(self):
        self.ensure_one()
        self.forward_id.action_budget_balance_forward()


class BudgetBalanceForwardInfoLine(models.TransientModel):
    _name = "budget.balance.forward.info.line"
    _description = "Budget Balance Forward Info Line"

    forward_info_id = fields.Many2one(
        comodel_name="budget.balance.forward.info",
        index=True,
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    analytic_account_id = fields.Many2one(
        string="Forward to Analytic",
        comodel_name="account.analytic.account",
        readonly=True,
    )
    analytic_plan = fields.Many2one(
        comodel_name="account.analytic.plan",
        related="analytic_account_id.plan_id",
        readonly=True,
    )
    initial_available = fields.Monetary(
        readonly=True,
    )
    initial_commit = fields.Monetary(
        string="Initial Commitment",
        related="analytic_account_id.initial_commit",
        readonly=True,
    )
    amount_balance = fields.Monetary(
        string="Balance",
        compute="_compute_amount_balance",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="forward_info_id.currency_id",
        readonly=True,
    )

    def _compute_amount_balance(self):
        for rec in self:
            rec.amount_balance = rec.initial_available - rec.initial_commit
