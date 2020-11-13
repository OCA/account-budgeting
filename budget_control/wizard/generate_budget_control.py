# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class GenerateBudgetControl(models.TransientModel):
    _name = "generate.budget.control"
    _description = "Generate Budget Control Sheets"

    budget_period_id = fields.Many2one(
        comodel_name="budget.period",
        required=True,
        default=lambda self: self.env["budget.period"].browse(
            self._context.get("active_id")
        ),
        ondelete="cascade",
    )
    budget_id = fields.Many2one(
        comodel_name="mis.budget",
        related="budget_period_id.mis_budget_id",
        readonly=True,
    )
    state = fields.Selection(
        [("choose", "choose"), ("get", "get")],
        default="choose",
    )
    analytic_group_ids = fields.Many2many(
        comodel_name="account.analytic.group",
        relation="analytic_group_generate_budget_control_rel",
        column1="wizard_id",
        column2="group_id",
    )
    all_analytic_accounts = fields.Boolean(
        help="Generate budget control sheet for all missing analytic account",
    )
    analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        relation="analytic_generate_budget_control_rel",
        column1="wizard_id",
        column2="anlaytic_id",
        domain="[('group_id', 'in', analytic_group_ids)]",
    )
    init_budget_commit = fields.Boolean(
        string="Initial Budget By Commitment",
        help="If checked, the newly created budget control sheet will has "
        "initial budget equal to current budget commitment of its year.",
    )
    result_analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        relation="result_analytic_generate_budget_control_rel",
        column1="wizard_id",
        column2="anlaytic_id",
        readonly=True,
        help="Analytics not created by this operation, as they already exisits",
    )
    result_budget_control_ids = fields.Many2many(
        comodel_name="budget.control",
        relation="result_budget_generate_budget_control_rel",
        column1="wizard_id",
        column2="budget_control_id",
        readonly=True,
        help="Budget Control Sheets created by this operation",
    )

    @api.onchange("all_analytic_accounts", "analytic_group_ids")
    def _onchange_analytic_accounts(self):
        """Auto fill analytic_account_ids."""
        AnalyticAccount = self.env["account.analytic.account"]
        self.analytic_account_ids = False
        if self.all_analytic_accounts:
            self.analytic_account_ids = AnalyticAccount.search(
                [("group_id", "in", self.analytic_group_ids.ids)]
            )

    def action_generate_budget_control(self):
        """Create new draft budget control sheet for all selected analytics."""
        self.ensure_one()
        BudgetControl = self.env["budget.control"]
        # Find existing controls, so we can skip.
        existing_analytics = BudgetControl.search(
            [
                ("budget_id", "=", self.budget_id.id),
                ("analytic_account_id", "in", self.analytic_account_ids.ids),
            ]
        ).mapped("analytic_account_id")
        # Create budget controls that are not already exists
        vals = []
        for analytic in self.analytic_account_ids - existing_analytics:
            plan_date_range = self.budget_period_id.plan_date_range_type_id
            vals.append(
                {
                    "name": "{} :: {}".format(
                        self.budget_period_id.name, analytic.name
                    ),
                    "budget_id": self.budget_id.id,
                    "analytic_account_id": analytic.id,
                    "plan_date_range_type_id": plan_date_range.id,
                }
            )
        budget_controls = BudgetControl.create(vals)
        budget_controls.do_init_budget_commit(self.init_budget_commit)
        # Return result
        self.write(
            {
                "state": "get",
                "result_analytic_account_ids": [(6, 0, existing_analytics.ids)],
                "result_budget_control_ids": [(6, 0, budget_controls.ids)],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }

    def action_view_budget_control(self):
        self.ensure_one()
        action = self.env.ref("budget_control.budget_control_action")
        result = action.read()[0]
        result["domain"] = [("id", "in", self.result_budget_control_ids.ids)]
        return result
