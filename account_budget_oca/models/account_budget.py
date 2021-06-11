# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from_string = fields.Datetime.from_string


# ---------------------------------------------------------
# Budgets
# ---------------------------------------------------------
class AccountBudgetPost(models.Model):
    _name = "account.budget.post"
    _order = "name"
    _description = "Budgetary Position"

    name = fields.Char(required=True)
    account_ids = fields.Many2many(
        comodel_name="account.account",
        relation="account_budget_rel",
        column1="budget_id",
        column2="account_id",
        string="Accounts",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
    )
    crossovered_budget_line_ids = fields.One2many(
        comodel_name="crossovered.budget.lines",
        inverse_name="general_budget_id",
        string="Budget Lines",
    )
    company_id = fields.Many2one(
        comodel_name="res.company", required=True, default=lambda self: self.env.company
    )

    def _check_account_ids(self, vals):
        # Raise an error to prevent the account.budget.post to have not
        # specified account_ids.
        # This check is done on create because require=True doesn't work on
        # Many2many fields.
        if "account_ids" in vals:
            account_ids = self.new({"account_ids": vals["account_ids"]}).account_ids
        else:
            account_ids = self.account_ids
        if not account_ids:
            raise ValidationError(_("The budget must have at least one account."))

    @api.model
    def create(self, vals):
        self._check_account_ids(vals)
        return super().create(vals)

    def write(self, vals):
        self._check_account_ids(vals)
        return super().write(vals)


class CrossoveredBudget(models.Model):
    _name = "crossovered.budget"
    _description = "Budget"
    _inherit = ["mail.thread"]

    name = fields.Char(
        string="Budget Name", required=True, states={"done": [("readonly", True)]}
    )
    creating_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        default=lambda self: self.env.user,
    )
    date_from = fields.Date(
        string="Start Date", required=True, states={"done": [("readonly", True)]}
    )
    date_to = fields.Date(
        string="End Date", required=True, states={"done": [("readonly", True)]}
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("cancel", "Cancelled"),
            ("confirm", "Confirmed"),
            ("validate", "Validated"),
            ("done", "Done"),
        ],
        string="Status",
        default="draft",
        index=True,
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    crossovered_budget_line_ids = fields.One2many(
        comodel_name="crossovered.budget.lines",
        inverse_name="crossovered_budget_id",
        string="Budget Lines",
        states={"done": [("readonly", True)]},
        copy=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company", required=True, default=lambda self: self.env.company
    )

    def action_budget_confirm(self):
        self.write({"state": "confirm"})

    def action_budget_draft(self):
        self.write({"state": "draft"})

    def action_budget_validate(self):
        self.write({"state": "validate"})

    def action_budget_cancel(self):
        self.write({"state": "cancel"})

    def action_budget_done(self):
        self.write({"state": "done"})


class CrossoveredBudgetLines(models.Model):
    _name = "crossovered.budget.lines"
    _description = "Budget Line"

    crossovered_budget_id = fields.Many2one(
        comodel_name="crossovered.budget",
        string="Budget",
        ondelete="cascade",
        index=True,
        required=True,
    )
    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account")
    general_budget_id = fields.Many2one(
        comodel_name="account.budget.post", string="Budgetary Position", required=True
    )
    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    paid_date = fields.Date()
    planned_amount = fields.Float(required=True, digits=0)
    practical_amount = fields.Float(compute="_compute_practical_amount", digits=0)
    theoretical_amount = fields.Float(compute="_compute_theoretical_amount", digits=0)
    percentage = fields.Float(compute="_compute_percentage", string="Achievement")
    company_id = fields.Many2one(
        related="crossovered_budget_id.company_id", store=True, readonly=True
    )

    @api.depends(
        "general_budget_id.account_ids", "date_from", "date_to", "analytic_account_id"
    )
    def _compute_practical_amount(self):
        for line in self:
            result = 0.0
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = line.date_to
            date_from = line.date_from
            if line.analytic_account_id.id:
                self.env.cr.execute(
                    """
                    SELECT SUM(amount)
                    FROM account_analytic_line
                    WHERE account_id=%s
                        AND (date between %s
                        AND %s)
                        AND general_account_id=ANY(%s)""",
                    (line.analytic_account_id.id, date_from, date_to, acc_ids),
                )
                result = self.env.cr.fetchone()[0] or 0.0
            line.practical_amount = result

    @api.depends("paid_date", "date_from", "date_to", "planned_amount")
    def _compute_theoretical_amount(self):
        today = fields.Datetime.now()
        for line in self:
            # Used for the report

            if line.paid_date:
                if from_string(line.date_to) <= from_string(line.paid_date):
                    theo_amt = 0.00
                else:
                    theo_amt = line.planned_amount
            elif line.date_from and line.date_to:
                line_timedelta = from_string(line.date_to) - from_string(line.date_from)
                elapsed_timedelta = from_string(today) - from_string(line.date_from)

                if elapsed_timedelta.days < 0:
                    # If the budget line has not started yet, theoretical
                    # amount should be zero
                    theo_amt = 0.00
                elif line_timedelta.days > 0 and from_string(today) < from_string(
                    line.date_to
                ):
                    # If today is between the budget line date_from and
                    # date_to
                    theo_amt = (
                        elapsed_timedelta.total_seconds()
                        / line_timedelta.total_seconds()
                    ) * line.planned_amount
                else:
                    theo_amt = line.planned_amount
            else:
                theo_amt = 0.00
            line.theoretical_amount = theo_amt

    @api.depends("theoretical_amount", "practical_amount")
    def _compute_percentage(self):
        for line in self:
            if line.theoretical_amount != 0.00:
                line.percentage = (
                    float((line.practical_amount or 0.0) / line.theoretical_amount)
                    * 100
                )
            else:
                line.percentage = 0.00
