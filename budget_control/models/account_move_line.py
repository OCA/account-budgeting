# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line", "budget.docline.mixin"]
    _budget_date_commit_fields = ["move_id.date"]
    _budget_move_model = "account.budget.move"
    _doc_rel = "move_id"

    can_commit = fields.Boolean(
        compute="_compute_can_commit",
    )
    budget_move_ids = fields.One2many(
        comodel_name="account.budget.move",
        inverse_name="move_line_id",
        string="Account Budget Moves",
    )

    @api.depends()
    def _compute_can_commit(self):
        super()._compute_can_commit()
        no_budget_moves = self.mapped("move_id").filtered("not_affect_budget")
        no_budget_moves.mapped("line_ids").update({"can_commit": False})

    def recompute_budget_move(self):
        for invoice_line in self:
            invoice_line.budget_move_ids.unlink()
            # Commit on invoice
            invoice_line.commit_budget()

    def _init_docline_budget_vals(self, budget_vals):
        self.ensure_one()
        if self.move_id.move_type == "entry":
            budget_vals["amount_currency"] = self.amount_currency
        else:
            sign = -1 if self.move_id.move_type in ("out_refund", "in_refund") else 1
            budget_vals["amount_currency"] = sign * self.price_unit * self.quantity
        budget_vals["tax_ids"] = self.tax_ids.ids
        # Document specific vals
        budget_vals.update(
            {
                "move_line_id": self.id,
                "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
            }
        )
        return super()._init_docline_budget_vals(budget_vals)

    def _valid_commit_state(self):
        states = ["posted"]
        return self.move_id.state in states
