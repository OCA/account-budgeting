# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class BudgetTransfer(models.Model):
    _name = "budget.transfer"
    _inherit = ["mail.thread"]
    _description = "Budget Transfer"

    name = fields.Char(
        default="/",
        index=True,
        copy=False,
        required=True,
        readonly=True,
    )
    budget_period_id = fields.Many2one(
        comodel_name="budget.period",
        string="Budget Year",
        default=lambda self: self._get_budget_period(),
        required=True,
        readonly=True,
    )
    mis_budget_id = fields.Many2one(
        comodel_name="mis.budget",
        related="budget_period_id.mis_budget_id",
        readonly=True,
    )
    transfer_item_ids = fields.One2many(
        comodel_name="budget.transfer.item",
        inverse_name="transfer_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submit", "Submitted"),
            ("transfer", "Transferred"),
            ("reverse", "Reversed"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("budget.transfer") or "/"
            )
        return super().create(vals)

    def unlink(self):
        """Check state draft can delete only."""
        if any(rec.state != "draft" for rec in self):
            raise UserError(
                _("You are trying to delete a record that is still referenced!")
            )
        return super().unlink()

    @api.model
    def _get_budget_period(self):
        today = fields.Date.context_today(self)
        BudgetPeriod = self.env["budget.period"]
        budget_period = BudgetPeriod.search(
            [("bm_date_from", "<=", today), ("bm_date_to", ">=", today)],
            limit=1,
        )
        return budget_period

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_submit(self):
        item_ids = self.mapped("transfer_item_ids")
        for transfer in item_ids:
            transfer._check_constraint_transfer()
        self.write({"state": "submit"})

    def action_transfer(self):
        self.mapped("transfer_item_ids").transfer()
        self._check_budget_control()
        self.write({"state": "transfer"})

    def action_reverse(self):
        self.mapped("transfer_item_ids").reverse()
        self._check_budget_control()
        self.write({"state": "reverse"})

    def _check_budget_available_analytic(self, budget_controls):
        for budget_ctrl in budget_controls:
            balance = budget_ctrl.get_report_amount(["total"], ["Available"])
            if balance < 0.0:
                raise ValidationError(
                    _("This transfer will result in negative budget balance " "for %s")
                    % budget_ctrl.name
                )
        return True

    def _check_budget_control(self):
        """Ensure no budget control will result in negative balance."""
        transfers = self.mapped("transfer_item_ids")
        budget_controls = transfers.mapped(
            "source_budget_control_id"
        ) | transfers.mapped("target_budget_control_id")
        # Control all analytic
        self._check_budget_available_analytic(budget_controls)
