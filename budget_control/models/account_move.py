# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    not_affect_budget = fields.Boolean(
        help="If check, lines does not affect the budget"
    )
    budget_move_ids = fields.One2many(
        comodel_name="account.budget.move",
        inverse_name="move_id",
        string="Account Budget Moves",
    )

    def recompute_budget_move(self):
        self.mapped("invoice_line_ids").recompute_budget_move()

    def _write(self, vals):
        """
        - Commit budget when state changes to actual
        - Cancel/Draft document should delete all budget commitment
        """
        res = super()._write(vals)
        if vals.get("state") in ("posted", "cancel", "draft"):
            BudgetControl = self.env["budget.control"]
            invoice_line = self.mapped("invoice_line_ids")
            analytic_account_ids = invoice_line.mapped("analytic_account_id")
            budget_control = BudgetControl.search(
                [("analytic_account_id", "in", analytic_account_ids.ids)]
            )
            if any(state != "done" for state in budget_control.mapped("state")):
                raise UserError(_("Analytic Account is not Controlled"))
            if self.move_type == "entry":
                invoice_line = invoice_line.filtered(lambda l: l.analytic_account_id)
            for line in invoice_line:
                line.commit_budget()
        return res

    def _move_type_budget(self):
        """For hooks, default check budget following
        - Vedor Bills
        - Customer Refund
        - Journal Entries
        """
        self.ensure_one()
        return ("in_invoice", "out_refund", "entry")

    def action_post(self):
        res = super().action_post()
        self.flush()
        BudgetPeriod = self.env["budget.period"]
        move_check_budget = self.filtered(
            lambda l: not l.not_affect_budget
            and l.move_type in self._move_type_budget()
        )
        for doc in move_check_budget:
            BudgetPeriod.check_budget(doc.budget_move_ids)
        return res
