# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    name_with_budget_period = fields.Char(
        compute="_compute_name_with_budget_period",
        store=True,
        help="This field hold analytic name with budget period indicator.\n"
        "This name will work with name_get() and name_search() to ensure usability",
    )
    budget_period_id = fields.Many2one(
        comodel_name="budget.period",
        index=True,
    )
    budget_control_ids = fields.One2many(
        string="Budget Control(s)",
        comodel_name="budget.control",
        inverse_name="analytic_account_id",
        readonly=True,
    )
    bm_date_from = fields.Date(
        string="Date From",
        compute="_compute_bm_date",
        store=True,
        readonly=False,
        tracking=True,
        help="Budget commit date must conform with this date",
    )
    bm_date_to = fields.Date(
        string="Date To",
        compute="_compute_bm_date",
        store=True,
        readonly=False,
        tracking=True,
        help="Budget commit date must conform with this date",
    )
    auto_adjust_date_commit = fields.Boolean(
        string="Auto Adjust Commit Date",
        default=True,
        help="Date From and Date To is used to determine valid date range of "
        "this analytic account when using with budgeting system. If this data range "
        "is setup, but the budget system set date_commit out of this date range "
        "it it can be adjusted automatically.",
    )
    amount_budget = fields.Monetary(
        string="Budgeted",
        compute="_compute_amount_budget_info",
        help="Sum of amount plan",
    )
    amount_consumed = fields.Monetary(
        string="Consumed",
        compute="_compute_amount_budget_info",
        help="Consumed = Total Commitments + Actual",
    )
    amount_balance = fields.Monetary(
        string="Available",
        compute="_compute_amount_budget_info",
        help="Available = Total Budget - Consumed",
    )
    initial_available = fields.Monetary(
        copy=False,
        readonly=True,
        tracking=True,
        help="Initial Balance come from carry forward available accumulated",
    )
    initial_commit = fields.Monetary(
        string="Initial Commitment",
        copy=False,
        readonly=True,
        tracking=True,
        help="Initial Balance from carry forward commitment",
    )

    @api.depends("name", "budget_period_id")
    def _compute_name_with_budget_period(self):
        for rec in self:
            if rec.budget_period_id:
                rec.name_with_budget_period = "{}: {}".format(
                    rec.budget_period_id.name, rec.name
                )
            else:
                rec.name_with_budget_period = rec.name

    def name_get(self):
        res = []
        for analytic in self:
            name = analytic.name_with_budget_period
            if analytic.code:
                name = ("[%(code)s] %(name)s") % {"code": analytic.code, "name": name}
            if analytic.partner_id:
                name = _("%(name)s - %(partner)s") % {
                    "name": name,
                    "partner": analytic.partner_id.commercial_partner_id.name,
                }
            res.append((analytic.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        # Make a search with default criteria
        args = args or []
        names1 = super(models.Model, self).name_search(
            name=name, args=args, operator=operator, limit=limit
        )
        # Make search with name_with_budget_period
        names2 = []
        if name:
            domain = args + [("name_with_budget_period", "=ilike", name + "%")]
            names2 = self.search(domain, limit=limit).name_get()
        # Merge both results
        return list(set(names1) | set(names2))[:limit]

    def _filter_by_analytic_account(self, val):
        if val["analytic_account_id"][0] == self.id:
            return True
        return False

    def _compute_amount_budget_info(self):
        """Note: This method is similar to BCS._compute_budget_info"""
        BudgetPeriod = self.env["budget.period"]
        MonitorReport = self.env["budget.monitor.report"]
        query = BudgetPeriod._budget_info_query()
        analytic_ids = self.ids
        # Retrieve budgeting data for a list of budget_control
        domain = [("analytic_account_id", "in", analytic_ids)]
        # Optional filters by context
        ctx = self.env.context.copy()
        if ctx.get("no_fwd_commit"):
            domain.append(("fwd_commit", "=", False))
        if ctx.get("budget_period_ids"):
            domain.append(("budget_period_id", "in", ctx["budget_period_ids"]))
        # --
        admin_uid = self.env.ref("base.user_admin").id
        dataset_all = MonitorReport.with_user(admin_uid).read_group(
            domain=domain,
            fields=["analytic_account_id", "amount_type", "amount"],
            groupby=["analytic_account_id", "amount_type"],
            lazy=False,
        )
        for rec in self:
            # Filter according to budget_control parameter
            dataset = list(
                filter(lambda l: rec._filter_by_analytic_account(l), dataset_all)
            )
            # Get data from dataset
            budget_info = BudgetPeriod.get_budget_info_from_dataset(query, dataset)
            rec.amount_budget = budget_info["amount_budget"]
            rec.amount_consumed = budget_info["amount_consumed"]
            rec.amount_balance = rec.amount_budget - rec.amount_consumed

    def _find_next_analytic(self, next_date_range):
        self.ensure_one()
        Analytic = self.env["account.analytic.account"]
        next_analytic = Analytic.search(
            [("name", "=", self.name), ("bm_date_from", "=", next_date_range)]
        )
        return next_analytic

    def _update_val_analytic(self, next_analytic, next_date_range):
        BudgetPeriod = self.env["budget.period"]
        type_id = next_analytic.budget_period_id.plan_date_range_type_id
        period_id = BudgetPeriod.search(
            [
                ("bm_date_from", "=", next_date_range),
                ("plan_date_range_type_id", "=", type_id.id),
            ]
        )
        return {"budget_period_id": period_id.id}

    def _auto_create_next_analytic(self, next_date_range):
        self.ensure_one()
        next_analytic = self.copy()
        val_update = self._update_val_analytic(next_analytic, next_date_range)
        next_analytic.write(val_update)
        return next_analytic

    def next_year_analytic(self, auto_create=True):
        """Find next analytic from analytic date_to + 1,
        if bm_date_to = False, this is an open end analytic, always return False"""
        self.ensure_one()
        if not self.bm_date_to:
            return False
        next_date_range = self.bm_date_to + relativedelta(days=1)
        next_analytic = self._find_next_analytic(next_date_range)
        if not next_analytic and auto_create:
            next_analytic = self._auto_create_next_analytic(next_date_range)
        return next_analytic

    def _check_budget_control_status(self, budget_period_id=False):
        """Warning for budget_control on budget_period, but not in controlled"""
        domain = [("analytic_account_id", "in", self.ids)]
        if budget_period_id:
            domain.append(("budget_period_id", "=", budget_period_id))
        budget_controls = self.env["budget.control"].search(domain)
        # Find analytics has no budget control sheet
        bc_analytics = budget_controls.mapped("analytic_account_id")
        no_bc_analytics = set(self) - set(bc_analytics)
        if no_bc_analytics:
            names = ", ".join([analytic.display_name for analytic in no_bc_analytics])
            raise UserError(
                _("Following analytics has no budget control sheet:\n%s") % names
            )
        # Find analytics has no controlled budget control sheet
        budget_controlled = budget_controls.filtered_domain([("state", "=", "done")])
        cbc_analytics = budget_controlled.mapped("analytic_account_id")
        no_cbc_analytics = set(self) - set(cbc_analytics)
        if no_cbc_analytics:
            names = ", ".join([analytic.display_name for analytic in no_cbc_analytics])
            raise UserError(
                _(
                    "Budget control sheet for following analytics are not in "
                    "control:\n%s"
                )
                % names
            )

    @api.depends("budget_period_id")
    def _compute_bm_date(self):
        """Default effective date, but changable"""
        for rec in self:
            rec.bm_date_from = rec.budget_period_id.bm_date_from
            rec.bm_date_to = rec.budget_period_id.bm_date_to

    def _auto_adjust_date_commit(self, docline):
        self.ensure_one()
        if self.auto_adjust_date_commit:
            if self.bm_date_from and self.bm_date_from > docline.date_commit:
                docline.date_commit = self.bm_date_from
            elif self.bm_date_to and self.bm_date_to < docline.date_commit:
                docline.date_commit = self.bm_date_to

    def action_edit_initial_available(self):
        return {
            "name": _("Edit Analytic Budget"),
            "type": "ir.actions.act_window",
            "res_model": "analytic.budget.edit",
            "view_mode": "form",
            "target": "new",
            "context": {"default_initial_available": self.initial_available},
        }
