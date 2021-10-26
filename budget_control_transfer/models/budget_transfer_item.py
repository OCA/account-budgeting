# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class BudgetTransferItem(models.Model):
    _name = "budget.transfer.item"
    _description = "Budget Transfer by Item"

    transfer_id = fields.Many2one(
        comodel_name="budget.transfer",
        ondelete="cascade",
        index=True,
    )
    mis_budget_id = fields.Many2one(
        comodel_name="mis.budget",
        related="transfer_id.mis_budget_id",
    )
    budget_period_id = fields.Many2one(
        comodel_name="budget.period",
        related="transfer_id.budget_period_id",
    )
    source_budget_control_id = fields.Many2one(
        comodel_name="budget.control",
        string="Source",
        domain="[('budget_period_id', '=', budget_period_id)]",
        required=True,
        index=True,
    )
    target_budget_control_id = fields.Many2one(
        comodel_name="budget.control",
        string="Target",
        domain="[('budget_period_id', '=', budget_period_id)]",
        required=True,
        index=True,
    )
    source_amount_available = fields.Float(
        compute="_compute_amount_available",
        store="True",
        readonly=True,
    )
    target_amount_available = fields.Float(
        compute="_compute_amount_available",
        store="True",
        readonly=True,
    )
    source_state = fields.Selection(
        related="source_budget_control_id.state",
        string="Source State",
        store=True,
    )
    target_state = fields.Selection(
        related="target_budget_control_id.state",
        string="Target State",
        store=True,
    )
    amount = fields.Float(
        string="Transfer Amount",
    )
    state = fields.Selection(related="transfer_id.state", store=True)

    def _get_budget_balance(self, budget_ctrl, kpi_name):
        balance = budget_ctrl and budget_ctrl.get_report_amount(
            [kpi_name], ["Available"]
        )
        return balance

    def _get_source_transfer_budget_control(self):
        source_budget_ctrl = self.source_budget_control_id
        target_budget_ctrl = self.target_budget_control_id
        return source_budget_ctrl, target_budget_ctrl

    @api.depends("source_budget_control_id", "target_budget_control_id")
    def _compute_amount_available(self):
        for transfer in self:
            (
                source_budget_ctrl,
                target_budget_ctrl,
            ) = transfer._get_source_transfer_budget_control()
            transfer.source_amount_available = source_budget_ctrl.amount_balance
            transfer.target_amount_available = target_budget_ctrl.amount_balance

    def _check_constraint_transfer(self):
        self.ensure_one()
        if self.source_budget_control_id == self.target_budget_control_id:
            raise UserError(
                _("You can not transfer from the same budget control sheet!")
            )
        if self.amount <= 0.0:
            raise UserError(_("Transfer amount must be positive!"))
        if self.amount > self.source_amount_available:
            raise UserError(
                _(
                    "Transfer amount can not be exceeded {:,.2f}".format(
                        self.source_amount_available
                    )
                )
            )

    def transfer(self):
        for transfer in self:
            transfer._check_constraint_transfer()
            transfer.source_budget_control_id.released_amount -= transfer.amount
            transfer.target_budget_control_id.released_amount += transfer.amount
        # Final check
        source_amounts = self.mapped("source_budget_control_id.released_amount")
        if list(filter(lambda a: a < 0, source_amounts)):
            raise ValidationError(_("Negative source amount after transfer!"))

    def reverse(self):
        for transfer in self:
            transfer.source_budget_control_id.released_amount += transfer.amount
            transfer.target_budget_control_id.released_amount -= transfer.amount

    @api.constrains("source_state", "target_state")
    def _check_state(self):
        """
        Condition to constrain
        - Budget Transfer have to state 'draft' or 'submit'
        - Budget Control Sheet have to state 'draft' only.
        """
        BudgetControl = self.env["budget.control"]
        for transfer in self:
            state_transfer = transfer.transfer_id.state in ["draft", "submit"]
            source_budget = (
                transfer.source_state != "draft"
                and transfer.source_budget_control_id
                or BudgetControl
            )
            target_budget = (
                transfer.target_state != "draft"
                and transfer.target_budget_control_id
                or BudgetControl
            )
            budget_not_draft = source_budget + target_budget
            budget_not_draft = ", ".join(budget_not_draft.mapped("name"))
            if state_transfer and budget_not_draft:
                raise UserError(
                    _(
                        "Following budget controls must be in state 'Draft', "
                        "before transferring.\n{}".format(budget_not_draft)
                    )
                )
