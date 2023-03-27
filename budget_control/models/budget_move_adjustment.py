# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BudgetMoveAdjustment(models.Model):
    _name = "budget.move.adjustment"
    _inherit = ["mail.thread"]
    _description = "Budget Moves Adjustment"

    budget_move_ids = fields.One2many(
        comodel_name="account.budget.move",
        inverse_name="adjust_id",
        string="Account Budget Moves",
    )
    name = fields.Char(
        default="/",
        index=True,
        copy=False,
        required=True,
        readonly=True,
    )
    description = fields.Text(
        readonly=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
    )
    adjust_item_ids = fields.One2many(
        comodel_name="budget.move.adjustment.item",
        inverse_name="adjust_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
    )
    date_commit = fields.Date(
        string="Budget Commit Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.user.company_id.currency_id,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Adjusted"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    @api.model
    def create(self, vals):
        """Generate a new name using the 'budget.move.adjustment' sequence"""
        if vals.get("name", "/") == "/":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("budget.move.adjustment") or "/"
            )
        return super().create(vals)

    def unlink(self):
        """Check that only records with state 'draft' can be deleted."""
        if any(rec.state != "draft" for rec in self):
            raise UserError(
                _("You are trying to delete a record that is still referenced!")
            )
        return super().unlink()

    def action_draft(self):
        self.write({"state": "draft"})

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_adjust(self):
        res = self.write({"state": "done"})
        BudgetPeriod = self.env["budget.period"]
        for doc in self:
            BudgetPeriod.check_budget(doc.adjust_item_ids)
        return res

    def recompute_budget_move(self):
        self.mapped("adjust_item_ids").recompute_budget_move()

    def close_budget_move(self):
        self.mapped("adjust_item_ids").close_budget_move()

    def write(self, vals):
        """
        - Commit budget when state changes to done
        - Cancel/Draft document should delete all budget commitment
        """
        res = super().write(vals)
        if vals.get("state") in ("done", "cancel", "draft"):
            doclines = self.mapped("adjust_item_ids")
            if vals.get("state") in ("cancel", "draft"):
                doclines.write({"date_commit": False})
            doclines.recompute_budget_move()
        return res


class BudgetMoveAdjustmentItem(models.Model):
    _name = "budget.move.adjustment.item"
    _inherit = ["budget.docline.mixin"]
    _description = "Budget Moves Adjustment Lines"
    _budget_date_commit_fields = ["adjust_id.date_commit"]
    _budget_move_model = "account.budget.move"
    _doc_rel = "adjust_id"

    adjust_id = fields.Many2one(
        comodel_name="budget.move.adjustment",
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(string="Description")
    budget_move_ids = fields.One2many(
        comodel_name="account.budget.move",
        inverse_name="adjust_item_id",
        string="Account Budget Moves",
    )
    adjust_type = fields.Selection(
        selection=[
            ("consume", "Consume"),
            ("release", "Release"),
        ],
        default="consume",
        required=True,
        help="* Consume: Decrease budget of selected analtyic\n"
        "* Release: Increase budget of selected analtyic",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        required=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        required=True,
        index=True,
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag",
        string="Analytic Tags",
    )
    currency_id = fields.Many2one(
        related="adjust_id.currency_id",
        readonly=True,
    )
    amount = fields.Monetary(
        help="Amount as per company currency",
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.account_id = self.product_id._get_product_accounts()["expense"]
        self.name = self.product_id.name

    @api.depends("amount")
    def _compute_amount_balance(self):
        if self.filtered(lambda l: l.amount <= 0):
            raise UserError(_("Given amount must be positive"))
        for rec in self:
            # If the adjust type is 'release', negate the amount, else leave it as is
            rec.amount = -rec.amount if rec.adjust_type == "release" else rec.amount

    def recompute_budget_move(self):
        for item in self:
            item.budget_move_ids.unlink()
            item.commit_budget()

    def _init_docline_budget_vals(self, budget_vals):
        self.ensure_one()
        budget_vals["amount_currency"] = (
            -self.amount if self.adjust_type == "release" else self.amount
        )
        # Document specific values
        budget_vals.update(
            {
                "adjust_item_id": self.id,
                "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
            }
        )
        return super()._init_docline_budget_vals(budget_vals)

    def _valid_commit_state(self):
        return self.adjust_id.state == "done"
