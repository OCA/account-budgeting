# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class BudgetPlan(models.Model):
    _name = "budget.plan"
    _inherit = ["mail.thread"]
    _description = "Budget Plan"
    _order = "id desc"

    name = fields.Char(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
    )
    budget_period_id = fields.Many2one(
        comodel_name="budget.period",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_from = fields.Date(related="budget_period_id.bm_date_from")
    date_to = fields.Date(related="budget_period_id.bm_date_to")
    budget_control_ids = fields.One2many(
        comodel_name="budget.control",
        compute="_compute_budget_control",
    )
    budget_control_count = fields.Integer(
        string="# of Budget Control",
        compute="_compute_budget_control",
        help="Count budget control in Plan",
    )
    total_amount = fields.Monetary(compute="_compute_total_amount")
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.user.company_id,
        required=False,
        string="Company",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency", related="company_id.currency_id"
    )
    line_ids = fields.One2many(
        comodel_name="budget.plan.line",
        inverse_name="plan_id",
        copy=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        context={"active_test": False},
    )
    active = fields.Boolean(default=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )

    @api.depends("line_ids")
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped("amount"))

    @api.depends("line_ids")
    def _compute_budget_control(self):
        """Find all budget controls of the same period"""
        for rec in self.with_context(active_test=False).sudo():
            rec.budget_control_ids = rec.line_ids.mapped("budget_control_ids")
            rec.budget_control_count = len(rec.line_ids.mapped("budget_control_ids"))

    def _update_amount_consumed(self):
        self.ensure_one()
        for line in self.line_ids:
            # find consumed amount from budget control
            active_control = line._find_budget_controls()
            if len(active_control) > 1:
                raise UserError(
                    _("%s should have only 1 active budget control")
                    % line.analytic_account_id.display_name
                )
            line.amount_consumed = active_control.amount_consumed
            line.released_amount = active_control.released_amount

    def action_update_plan(self):
        """This function will update amount from budget control to plan lines
        and create new plan line (if any)"""
        Analytic = self.env["account.analytic.account"]
        for rec in self:
            # update amount lines
            rec._update_amount_consumed()
            plan_analytic = rec._get_analytic_plan()
            # search analytic is not add in plan line
            new_analytic = Analytic.search(
                [
                    ("bm_date_from", "<=", rec.date_to),
                    ("bm_date_to", ">=", rec.date_from),
                    ("id", "not in", plan_analytic.ids),
                ]
            )
            lines = []
            for new_aa in new_analytic:
                active_control = new_aa.budget_control_ids.filtered(
                    lambda l: l.budget_period_id == rec.budget_period_id
                )
                lines.append(
                    (
                        0,
                        0,
                        {
                            "analytic_account_id": new_aa.id,
                            "amount_consumed": active_control.amount_consumed,
                            "released_amount": active_control.released_amount,
                        },
                    )
                )
            rec.write({"line_ids": lines})

    def button_open_budget_control(self):
        self.ensure_one()
        ctx = self._context.copy()
        ctx.update(
            {
                "create": False,
                "active_test": False,
                "search_default_current_period": False,
            }
        )
        action = {
            "name": _("Budget Control Sheet"),
            "type": "ir.actions.act_window",
            "res_model": "budget.control",
            "context": ctx,
        }
        budget_controls = self.with_context(active_test=False).budget_control_ids
        if len(budget_controls) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": budget_controls.id,
                }
            )
        else:
            action.update(
                {
                    "view_mode": "list,form",
                    "domain": [("id", "in", budget_controls.ids)],
                }
            )
        return action

    def _get_analytic_plan(self):
        return self.line_ids.mapped("analytic_account_id")

    def _get_context_wizard(self):
        ctx = self._context.copy()
        ctx.update(
            {
                "active_model": "budget.period",
                "active_id": self.budget_period_id.id,
            }
        )
        return ctx

    def _generate_budget_control(self, analytic_plan):
        GenerateBudgetControl = self.env["generate.budget.control"]
        ctx = self._get_context_wizard()
        budget_period = self.budget_period_id
        generate_budget = GenerateBudgetControl.with_context(**ctx).create(
            {
                "budget_period_id": budget_period.id,
                "template_id": budget_period.template_id.id,
                "budget_plan_id": self.id,
                "analytic_account_ids": [(6, 0, analytic_plan.ids)],
            }
        )
        budget_control_view = generate_budget.action_generate_budget_control()
        return budget_control_view

    def action_create_update_budget_control(self):
        self.ensure_one()
        analytic_plan = self._get_analytic_plan()
        budget_control_view = self._generate_budget_control(analytic_plan)
        self.line_ids._update_budget_control_data()
        return budget_control_view

    def check_plan_consumed(self):
        self.action_update_plan()
        prec_digits = self.env.user.company_id.currency_id.decimal_places
        for line in self.mapped("line_ids"):
            # Check amount + transferred is less than the amount consumed
            if (
                float_compare(
                    line.amount + line.budget_control_ids.transferred_amount,
                    line.amount_consumed,
                    precision_digits=prec_digits,
                )
                == -1
            ):
                raise UserError(
                    _("{} has amount less than consumed.").format(
                        line.analytic_account_id.display_name
                    )
                )
            line.allocated_amount = line.released_amount = line.amount

    def action_confirm(self):
        self.check_plan_consumed()
        self.write({"state": "confirm"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_draft(self):
        self.write({"state": "draft"})


class BudgetPlanLine(models.Model):
    _name = "budget.plan.line"
    _description = "Budget Plan Line"

    plan_id = fields.Many2one(
        comodel_name="budget.plan",
        index=True,
        ondelete="cascade",
    )
    budget_control_ids = fields.Many2many(
        comodel_name="budget.control",
        string="Related Budget Control(s)",
        compute="_compute_budget_control_ids",
        help="Note: It is intention for this field to compute in realtime",
    )
    budget_period_id = fields.Many2one(
        comodel_name="budget.period", related="plan_id.budget_period_id"
    )
    date_from = fields.Date(related="plan_id.date_from")
    date_to = fields.Date(related="plan_id.date_to")
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        required=True,
    )
    allocated_amount = fields.Float(string="Allocated", readonly=True)
    released_amount = fields.Float(string="Released", readonly=True)
    amount = fields.Float(string="New Amount")
    amount_consumed = fields.Float(string="Consumed", readonly=True)
    active_status = fields.Boolean(
        default=True, help="Activate/Deactivate when create/Update Budget Control"
    )

    def _domain_budget_control(self):
        self.ensure_one()
        if not self.budget_period_id:
            raise ValidationError(_("Please select 'Budget Period'"))
        return [
            ("date_from", "<=", self.budget_period_id.bm_date_from),
            ("date_to", ">=", self.budget_period_id.bm_date_to),
            ("analytic_account_id", "=", self.analytic_account_id.id),
        ]

    @api.depends("analytic_account_id.budget_control_ids")
    def _compute_budget_control_ids(self):
        """It is expected this to contain only"""
        BudgetControl = (
            self.env["budget.control"].with_context(active_test=False).sudo()
        )
        for rec in self.sudo():
            rec.budget_control_ids = BudgetControl.search(rec._domain_budget_control())

    def _update_budget_control_data(self):
        """Push data budget control, i.e., alloc amount, active status"""
        self.invalidate_cache()
        for rec in self:
            all_controls = rec.with_context(active_test=False).budget_control_ids
            # First, update the active budget_control
            budget_control = all_controls.filtered("active")
            # If no active budget control, find the newest inactive one
            if not budget_control:
                budget_control = all_controls.sorted("id")[-1:]  # last one
            # Update on if changed
            if (
                budget_control.allocated_amount != rec.allocated_amount
                or budget_control.active != rec.active_status
            ):
                budget_control.write(
                    {
                        "allocated_amount": rec.allocated_amount,
                        "active": rec.active_status,
                    }
                )
                budget_control.action_draft()

    def _find_budget_controls(self):
        return self.budget_control_ids
