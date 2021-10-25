# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class BudgetPlan(models.Model):
    _name = "budget.plan"
    _inherit = ["mail.thread"]
    _description = "Budget Plan"
    _order = "id desc"

    name = fields.Char(
        required=True,
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
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
    plan_line = fields.One2many(
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

    @api.depends("plan_line")
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.plan_line.mapped("amount"))

    def _compute_budget_control(self):
        """ Find all budget controls of the same period """
        for rec in self:
            rec.budget_control_ids = rec.plan_line.mapped("budget_control_ids")
            rec.budget_control_count = len(rec.budget_control_ids)

    def action_update_amount_consumed(self):
        for rec in self:
            for line in rec.plan_line:
                budget_control = line.budget_control_ids
                if len(budget_control) > 1:
                    raise UserError(
                        _("%s should have only 1 active budget control")
                        % line.analytic_account_id.display_name
                    )
                line.amount_consumed = budget_control.amount_consumed

    def button_open_budget_control(self):
        self.ensure_one()
        ctx = self._context.copy()
        ctx.update({"create": False, "active_test": True})
        action = {
            "name": _("Budget Control Sheet"),
            "type": "ir.actions.act_window",
            "res_model": "budget.control",
            "context": ctx,
        }
        if len(self.budget_control_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": self.budget_control_ids.id,
                }
            )
        else:
            action.update(
                {
                    "view_mode": "list,form",
                    "domain": [("id", "in", self.budget_control_ids.ids)],
                }
            )
        return action

    def action_generate_plan(self):
        self.ensure_one()
        Analytic = self.env["account.analytic.account"]
        plan_analytic = self.plan_line.mapped("analytic_account_id")
        analytic_ids = Analytic.search(
            [
                ("bm_date_from", "<=", self.date_to),
                ("bm_date_to", ">=", self.date_from),
                ("id", "not in", plan_analytic.ids),
            ]
        )
        if analytic_ids:
            lines = list(
                map(
                    lambda l: (0, 0, {"analytic_account_id": l.id}),
                    analytic_ids,
                )
            )
            self.write({"plan_line": lines})
        return True

    def _get_analytic_plan(self):
        return self.plan_line.mapped("analytic_account_id")

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
        generate_budget = GenerateBudgetControl.with_context(ctx).create(
            {
                "budget_period_id": budget_period.id,
                "mis_report_id": budget_period.report_id.id,
                "budget_id": budget_period.mis_budget_id.id,
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
        self.plan_line._update_budget_control_data()
        # self._update_active_budget_control(analytic_plan)
        return budget_control_view

    def action_confirm(self):
        self.action_update_amount_consumed()
        prec_digits = self.env.user.company_id.currency_id.decimal_places
        lines = self.mapped("plan_line")
        for line in lines:
            if (
                float_compare(
                    line.amount,
                    line.amount_consumed,
                    precision_digits=prec_digits,
                )
                == -1
            ):
                raise UserError(
                    _(
                        "{} has amount less than consumed.".format(
                            line.analytic_account_id.display_name
                        )
                    )
                )
            line.allocated_amount = line.released_amount = line.amount
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
    active_status = fields.Boolean(default=True)

    def _domain_budget_control(self):
        self.ensure_one()
        return [
            ("date_from", "<=", self.budget_period_id.bm_date_from),
            ("date_to", ">=", self.budget_period_id.bm_date_to),
            ("analytic_account_id", "=", self.analytic_account_id.id),
            ("active", "=", True),
        ]

    def _compute_budget_control_ids(self):
        """ It is expected this to contain only """
        analytics = self.mapped("analytic_account_id")
        budget_controls = self.env["budget.control"].search(
            [("analytic_account_id", "in", analytics.ids)]
        )
        for rec in self:
            rec.budget_control_ids = budget_controls.filtered_domain(
                rec._domain_budget_control()
            )

    def _update_budget_control_data(self):
        """ Push data budget control, i.e., alloc amount, active status """
        self.invalidate_cache()
        for rec in self:
            rec.budget_control_ids.write(
                {
                    "allocated_amount": rec.allocated_amount,
                    "active": rec.active_status,
                }
            )
