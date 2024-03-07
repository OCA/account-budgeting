# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class BudgetTransferItem(models.Model):
    _name = "budget.transfer.item"
    _description = "Budget Transfer by Item"

    transfer_id = fields.Many2one(
        comodel_name="budget.transfer",
        ondelete="cascade",
        index=True,
    )
    budget_period_id = fields.Many2one(
        comodel_name="budget.period",
        related="transfer_id.budget_period_id",
    )
    budget_control_from_id = fields.Many2one(
        comodel_name="budget.control",
        string="From",
        domain="[('budget_period_id', '=', budget_period_id)]",
        required=True,
        index=True,
    )
    budget_control_to_id = fields.Many2one(
        comodel_name="budget.control",
        string="To",
        domain="[('budget_period_id', '=', budget_period_id)]",
        required=True,
        index=True,
    )
    amount_from_available = fields.Float(
        compute="_compute_amount_available",
        store="True",
        readonly=True,
    )
    amount_to_available = fields.Float(
        compute="_compute_amount_available",
        store="True",
        readonly=True,
    )
    state_from = fields.Selection(
        related="budget_control_from_id.state",
        string="State From",
        store=True,
    )
    state_to = fields.Selection(
        related="budget_control_to_id.state",
        string="State To",
        store=True,
    )
    amount = fields.Float(
        string="Transfer Amount",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.user.company_id.currency_id,
    )
    state = fields.Selection(related="transfer_id.state", store=True)

    def _get_budget_control_transfer(self):
        from_budget_ctrl = self.budget_control_from_id
        to_budget_ctrl = self.budget_control_to_id
        return from_budget_ctrl, to_budget_ctrl

    @api.depends("budget_control_from_id", "budget_control_to_id")
    def _compute_amount_available(self):
        for transfer in self:
            (
                from_budget_ctrl,
                to_budget_ctrl,
            ) = transfer._get_budget_control_transfer()
            transfer.amount_from_available = from_budget_ctrl.amount_balance
            transfer.amount_to_available = to_budget_ctrl.amount_balance

    def _check_constraint_transfer(self):
        self.ensure_one()
        if self.budget_control_from_id == self.budget_control_to_id:
            raise UserError(
                _("You can not transfer from the same budget control sheet!")
            )
        # check amount transfer must be positive
        if (
            float_compare(
                self.amount,
                0.0,
                precision_rounding=self.currency_id.rounding,
            )
            != 1
        ):
            raise UserError(_("Transfer amount must be positive!"))
        # check amount transfer must less than amount available (source budget)
        if (
            float_compare(
                self.amount,
                self.amount_from_available,
                precision_rounding=self.currency_id.rounding,
            )
            == 1
        ):
            raise UserError(
                _("Transfer amount can not be exceeded {:,.2f}").format(
                    self.amount_from_available
                )
            )

    def transfer(self):
        for transfer in self:
            transfer._check_constraint_transfer()
            transfer.budget_control_from_id.released_amount -= transfer.amount
            transfer.budget_control_to_id.released_amount += transfer.amount
        # Final check
        from_amounts = self.mapped("budget_control_from_id.released_amount")
        if list(filter(lambda a: a < 0, from_amounts)):
            raise ValidationError(_("Negative from amount after transfer!"))

    def reverse(self):
        for transfer in self:
            transfer.budget_control_from_id.released_amount += transfer.amount
            transfer.budget_control_to_id.released_amount -= transfer.amount

    @api.constrains("state_from", "state_to")
    def _check_state(self):
        """
        Condition to constrain
        - Budget Transfer have to state 'draft' or 'submit'
        - Budget Control Sheet have to state 'draft' only.
        """
        BudgetControl = self.env["budget.control"]
        for transfer in self:
            is_state_transfer_valid = transfer.transfer_id.state in ["draft", "submit"]
            from_budget_ctrl = (
                transfer.state_from != "draft"
                and transfer.budget_control_from_id
                or BudgetControl
            )
            to_budget_ctrl = (
                transfer.state_to != "draft"
                and transfer.budget_control_to_id
                or BudgetControl
            )
            budget_not_draft = from_budget_ctrl + to_budget_ctrl
            budget_not_draft = ", ".join(budget_not_draft.mapped("name"))
            if is_state_transfer_valid and budget_not_draft:
                raise UserError(
                    _(
                        "Following budget controls must be in state 'Draft', "
                        "before transferring.\n{}"
                    ).format(budget_not_draft)
                )
