# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BudgetControl(models.Model):
    _name = "budget.control"
    _description = "Budget Control"
    _inherit = ["mail.thread"]

    name = fields.Char(
        required=True,
    )
    assignee_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned To",
        domain=lambda self: [
            (
                "groups_id",
                "in",
                [self.env.ref("budget_control.group_budget_control_user").id],
            )
        ],
        tracking=True,
        states={"done": [("readonly", True)]},
        copy=False,
    )
    budget_id = fields.Many2one(
        comodel_name="mis.budget",
        string="MIS Budget",
        required=True,
        ondelete="restrict",
        domain=lambda self: self._get_mis_budget_domain(),
        help="List of mis.budget created by and linked to budget.period",
    )
    date_from = fields.Date(
        related="budget_id.date_from",
    )
    date_to = fields.Date(
        related="budget_id.date_to",
    )
    active = fields.Boolean(
        default=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        required=True,
        ondelete="restrict",
    )
    item_ids = fields.One2many(
        comodel_name="mis.budget.item",
        inverse_name="budget_control_id",
        string="Budget Items",
        copy=False,
    )
    plan_date_range_type_id = fields.Many2one(
        comodel_name="date.range.type",
        string="Plan Date Range",
        required=True,
    )
    init_budget_commit = fields.Boolean(
        string="Initial Budget By Commitment",
        help="If checked, the newly created budget control sheet will has "
        "initial budget equal to current budget commitment of its year.",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Controlled"), ("cancel", "Cancelled")],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        default="draft",
        tracking=True,
    )
    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "Name must be unique!"),
        (
            "budget_control_uniq",
            "UNIQUE(budget_id, analytic_account_id)",
            "Duplicated analytic account for the same budget!",
        ),
    ]

    @api.model
    def _get_mis_budget_domain(self):
        all_budget_periods = self.env["budget.period"].search([])
        return [("id", "in", all_budget_periods.mapped("mis_budget_id").ids)]

    def get_report_amount(self, kpi_names=None, col_names=None):
        self.ensure_one()
        BudgetPeriod = self.env["budget.period"]
        budget_period = BudgetPeriod.search([("mis_budget_id", "=", self.budget_id.id)])
        budget_period.ensure_one()
        return budget_period._get_amount(
            budget_period.report_instance_id.id,
            kpi_names=kpi_names,
            col_names=col_names,
            analytic_id=self.analytic_account_id.id,
        )

    def do_init_budget_commit(self, init):
        """Initialize budget with current commitment amount."""
        for plan in self:
            plan.update({"init_budget_commit": init})
            if not init or not plan.init_budget_commit or not plan.item_ids:
                continue
            init_date = min(plan.item_ids.mapped("date_from"))
            init_items = plan.item_ids.filtered(lambda l: l.date_from == init_date)
            for item in init_items:
                kpi_name = item.kpi_expression_id.kpi_id.name
                balance = plan.get_report_amount(
                    kpi_names=[kpi_name], col_names=["Available"]
                )
                item.update({"amount": -balance})

    @api.onchange("init_budget_commit")
    def _onchange_init_budget_commit(self):
        self.do_init_budget_commit(self.init_budget_commit)

    @api.model
    def create(self, vals):
        plan = super().create(vals)
        plan.prepare_budget_control_matrix()
        return plan

    def write(self, vals):
        # if any field in header changes, reset the plan matrix
        res = super().write(vals)
        fixed_fields = ["budget_id", "plan_date_range_type_id", "analytic_account_id"]
        change_fields = list(vals.keys())
        if list(set(fixed_fields) & set(change_fields)):
            self.prepare_budget_control_matrix()
        return res

    def action_done(self):
        self.write({"state": "done"})

    def action_draft(self):
        self.write({"state": "draft"})

    def action_cancel(self):
        self.write({"state": "cancel"})

    def prepare_budget_control_matrix(self):
        KpiExpression = self.env["mis.report.kpi.expression"]
        DateRange = self.env["date.range"]
        for plan in self:
            plan.item_ids.unlink()
            if not plan.plan_date_range_type_id:
                raise UserError(_("Please select range"))
            date_ranges = DateRange.search(
                [
                    ("type_id", "=", plan.plan_date_range_type_id.id),
                    ("date_start", ">=", plan.date_from),
                    ("date_end", "<=", plan.date_to),
                ]
            )
            kpi_expressions = KpiExpression.search(
                [
                    ("kpi_id.report_id", "=", plan.budget_id.report_id.id),
                    ("kpi_id.budgetable", "=", True),
                ]
            )
            items = []
            for date_range in date_ranges:
                for kpi_expression in kpi_expressions:
                    vals = {
                        "budget_id": plan.budget_id.id,
                        "kpi_expression_id": kpi_expression.id,
                        "date_range_id": date_range.id,
                        "date_from": date_range.date_start,
                        "date_to": date_range.date_end,
                        "analytic_account_id": plan.analytic_account_id.id,
                    }
                    items += [(0, 0, vals)]
            plan.write({"item_ids": items})
            # Also reset the carry over budget
            plan.init_budget_commit = False

    def _report_instance(self):
        self.ensure_one()
        budget_period = self.env["budget.period"].search(
            [("mis_budget_id", "=", self.budget_id.id)]
        )
        ctx = {"mis_report_filters": {}}
        if self.analytic_account_id:
            ctx["mis_report_filters"]["analytic_account_id"] = {
                "value": self.analytic_account_id.id,
            }
        return budget_period.report_instance_id.with_context(ctx)

    def preview(self):
        return self._report_instance().preview()

    def print_pdf(self):
        return self._report_instance().print_pdf()

    def export_xls(self):
        return self._report_instance().export_xls()
