# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"
    _docline_rel = "line_ids"
    _docline_type = "account"

    not_affect_budget = fields.Boolean(
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="If checked, lines does not create budget move",
    )
    budget_move_ids = fields.One2many(
        comodel_name="account.budget.move",
        inverse_name="move_id",
        string="Account Budget Moves",
    )
    return_amount_commit = fields.Boolean(
        help="This technical field is used to determine how to return budget "
        "to the original document (i.e., return back to PO).\n"
        "By default, system will use quantity to calculated for the returning amount. "
        "But with this flag, the amount commit of this document will be used instead.\n"
        "This is good when we want to ignore the quantity.\n"
        "This flag usually passed in when this invoice is created.",
    )

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        if res.get("journal_id"):
            journal = self.env["account.journal"].browse(res["journal_id"])
            res["not_affect_budget"] = journal.not_affect_budget
        return res

    @api.onchange("journal_id")
    def _onchange_not_affect_budget(self):
        self.not_affect_budget = self.journal_id.not_affect_budget

    def recompute_budget_move(self):
        self.mapped("invoice_line_ids").recompute_budget_move()

    def close_budget_move(self):
        self.mapped("invoice_line_ids").close_budget_move()

    @api.model
    def create(self, vals):
        """The default value of "Not affect budget" depends on journal.
        except in the case of a manaully created journal entry.
        """
        not_affect_budget = vals.get("not_affect_budget", "None")
        journal_id = vals.get("journal_id")
        if not_affect_budget == "None" and journal_id:
            journal = self.env["account.journal"].browse(journal_id)
            vals["not_affect_budget"] = journal.not_affect_budget
        return super().create(vals)

    def write(self, vals):
        """
        - Commit budget when state changes to actual
        - Cancel/Draft document should delete all budget commitment
        """
        res = super().write(vals)
        if vals.get("state") in ("posted", "cancel", "draft"):
            doclines = self.mapped("invoice_line_ids")
            if vals.get("state") in ("cancel", "draft"):
                # skip_account_move_synchronization = True, as this is account.move.line
                # skipping to avoid warning error when update date_commit
                doclines.with_context(skip_account_move_synchronization=True).write(
                    {"date_commit": False}
                )
            doclines.recompute_budget_move()
        return res

    def _filtered_move_check_budget(self):
        """For hooks, default check budget following
        - Vedor Bills
        - Customer Refund
        - Journal Entries
        """
        return self.filtered_domain(
            [("move_type", "in", ["in_invoice", "out_refund", "entry"])]
        )

    def action_post(self):
        res = super().action_post()
        self.flush()
        BudgetPeriod = self.env["budget.period"]
        for move in self._filtered_move_check_budget():
            BudgetPeriod.check_budget(move.line_ids)
        return res
