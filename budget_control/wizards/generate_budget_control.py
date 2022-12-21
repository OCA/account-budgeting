# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class GenerateBudgetControl(models.TransientModel):
    _name = "generate.budget.control"
    _description = "Generate Budget Control Sheets"

    budget_period_id = fields.Many2one(
        comodel_name="budget.period",
        required=True,
        ondelete="cascade",
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
    domain_analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        compute="_compute_domain_analytic_account_ids",
    )
    analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        relation="analytic_generate_budget_control_rel",
        column1="wizard_id",
        column2="anlaytic_id",
        domain="[('id', 'in', domain_analytic_account_ids)]",
    )
    init_budget_commit = fields.Boolean(
        string="Initial Budget By Commit Amount",
        help="If checked, the newly created budget control sheet will has "
        "initial budget equal to current budget commitment of its year.",
    )
    init_kpis = fields.Boolean(
        string="With Initial KPIs",
        help="When each budget control sheet is created, prefill lines "
        "with Intial KPIs",
    )
    use_all_kpis = fields.Boolean(string="Use All KPIs")
    template_id = fields.Many2one(
        comodel_name="budget.template",
        required=True,
        ondelete="cascade",
    )
    template_line_ids = fields.Many2many(
        comodel_name="budget.template.line",
        relation="kpi_generate_budget_control_rel",
        column1="wizard_id",
        column2="kpi_id",
        domain="[('template_id', '=', template_id)]",
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

    @api.model
    def default_get(self, default_fields):
        values = super().default_get(default_fields)
        period_id = self.env.context.get("active_id")
        period = self.env["budget.period"].browse(period_id)
        period._check_budget_period_date_range()
        values["budget_period_id"] = period.id
        values["template_id"] = period.template_id.id
        return values

    @api.depends("analytic_group_ids", "budget_period_id")
    def _compute_domain_analytic_account_ids(self):
        Analytic = self.env["account.analytic.account"]
        for rec in self:
            analytics = Analytic.search(
                [("group_id", "in", self.analytic_group_ids.ids)]
            )
            analytics = analytics.filtered_domain(
                [
                    "|",
                    ("bm_date_to", ">=", self.budget_period_id.bm_date_to),
                    ("bm_date_to", "=", False),
                ]
            )
            analytics = analytics.filtered_domain(
                [
                    "|",
                    ("bm_date_from", "<=", self.budget_period_id.bm_date_from),
                    ("bm_date_from", "=", False),
                ]
            )
            rec.domain_analytic_account_ids = analytics

    @api.onchange("all_analytic_accounts", "analytic_group_ids")
    def _onchange_analytic_accounts(self):
        """Auto fill analytic_account_ids."""
        self.analytic_account_ids = False
        if self.all_analytic_accounts:
            self.analytic_account_ids = self.domain_analytic_account_ids

    @api.onchange("use_all_kpis")
    def _onchange_use_all_kpis(self):
        self.template_line_ids = False
        if self.use_all_kpis:
            self.template_line_ids = self.env["budget.template.line"].search(
                [
                    ("template_id", "=", self.template_id.id),
                ]
            )

    def _get_budget_period_name(self):
        budget_name = "{} :: ".format(self.budget_period_id.name)
        return budget_name

    def _prepare_value_duplicate(self, vals):
        plan_date_range_id = self.budget_period_id.plan_date_range_type_id.id
        # Just in case not budget name
        budget_name = self._get_budget_period_name()
        use_all_kpis = self.use_all_kpis
        budget_period_id = self.budget_period_id.id
        template_lines = self.template_line_ids.ids
        return list(
            map(
                lambda l: {
                    "name": "{}".format(
                        budget_name
                        and budget_name + l["analytic_account_id"].name
                        or l["analytic_account_id"].name
                    ),
                    "analytic_account_id": l["analytic_account_id"].id,
                    "plan_date_range_type_id": plan_date_range_id,
                    "use_all_kpis": use_all_kpis,
                    "template_line_ids": template_lines,
                    "budget_period_id": budget_period_id,
                },
                vals,
            )
        )

    def _prepare_value(self, analytic):
        return [{"analytic_account_id": x} for x in analytic]

    def _prepare_budget_control_sheet(self, analytic):
        vals = self._prepare_value(analytic)
        return self._prepare_value_duplicate(vals)

    def _get_existing_budget(self):
        BudgetControl = self.env["budget.control"]
        existing_budget_controls = BudgetControl.search(
            [
                ("template_id", "=", self.template_id.id),
                ("budget_period_id", "=", self.id),
                ("analytic_account_id", "in", self.analytic_account_ids.ids),
            ]
        )
        return existing_budget_controls

    def _create_budget_controls(self, vals):
        return self.env["budget.control"].create(vals)

    def action_generate_budget_control(self):
        """Create new draft budget control sheet for all selected analytics."""
        self.ensure_one()
        # Find existing controls, so we can skip.
        existing_budget_controls = self._get_existing_budget()
        existing_analytics = existing_budget_controls.mapped("analytic_account_id")
        # Create budget controls that are not already exists
        new_analytic = self.analytic_account_ids - existing_analytics
        vals = self._prepare_budget_control_sheet(new_analytic)
        budget_controls = self._create_budget_controls(vals)
        budget_controls.prepare_budget_control_matrix()
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
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "budget_control.budget_control_action"
        )
        action["domain"] = [("id", "in", self.result_budget_control_ids.ids)]
        return action
