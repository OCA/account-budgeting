# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class BudgetControl(models.Model):
    _name = "budget.control"
    _description = "Budget Control"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "analytic_account_id"

    name = fields.Char(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
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
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    budget_period_id = fields.Many2one(
        comodel_name="budget.period",
        help="Budget Period that inline with date from/to",
        ondelete="restrict",
        readonly=True,
    )
    date_from = fields.Date(related="budget_period_id.bm_date_from")
    date_to = fields.Date(related="budget_period_id.bm_date_to")
    active = fields.Boolean(
        default=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        required=True,
        readonly=True,
        tracking=True,
        ondelete="restrict",
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag", string="Analytic Tags"
    )
    analytic_group = fields.Many2one(
        comodel_name="account.analytic.group",
        string="Analytic Group",
        related="analytic_account_id.group_id",
        store=True,
    )
    line_ids = fields.One2many(
        comodel_name="budget.control.line",
        inverse_name="budget_control_id",
        string="Budget Lines",
        copy=True,
        context={"active_test": False},
        readonly=True,
        states={
            "draft": [("readonly", False)],
            "submit": [("readonly", False)],
        },
    )
    plan_date_range_type_id = fields.Many2one(
        comodel_name="date.range.type",
        string="Plan Date Range",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    init_budget_commit = fields.Boolean(
        string="Initial Budget By Commitment",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="If checked, the newly created budget control sheet will has "
        "initial budget equal to current budget commitment of its year.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency", related="company_id.currency_id"
    )
    allocated_amount = fields.Monetary(
        string="Allocated",
        help="Initial total amount for plan",
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    released_amount = fields.Monetary(
        string="Released",
        compute="_compute_allocated_released_amount",
        store=True,
        tracking=True,
        help="Total amount for transfer current",
    )
    diff_amount = fields.Monetary(
        compute="_compute_diff_amount",
        help="Diff from Released - Budget",
    )
    # Total Amount
    amount_initial = fields.Monetary(
        string="Initial Balance",
        compute="_compute_initial_balance",
    )
    amount_budget = fields.Monetary(
        string="Budget",
        compute="_compute_budget_info",
        help="Sum of amount plan",
    )
    amount_actual = fields.Monetary(
        string="Actual",
        compute="_compute_budget_info",
        help="Sum of actual amount",
    )
    amount_commit = fields.Monetary(
        string="Commit",
        compute="_compute_budget_info",
        help="Total Commit = Sum of PR / PO / EX / AV commit (extension module)",
    )
    amount_consumed = fields.Monetary(
        string="Consumed",
        compute="_compute_budget_info",
        help="Consumed = Total Commitments + Actual",
    )
    amount_balance = fields.Monetary(
        string="Available",
        compute="_compute_budget_info",
        help="Available = Total Budget - Consumed",
    )
    template_id = fields.Many2one(
        comodel_name="budget.template",
        related="budget_period_id.template_id",
        readonly=True,
    )
    use_all_kpis = fields.Boolean(
        string="Use All KPIs",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    template_line_ids = fields.Many2many(
        string="KPIs",  # Template line = 1 KPI, name for users
        comodel_name="budget.template.line",
        relation="budget_template_line_budget_contol_rel",
        column1="budget_control_id",
        column2="template_line_id",
        domain="[('template_id', '=', template_id)]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submit", "Submitted"),
            ("done", "Controlled"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        default="draft",
        tracking=True,
    )
    transfer_item_ids = fields.Many2many(
        comodel_name="budget.transfer.item",
        string="Transfers",
        compute="_compute_transfer_item_ids",
    )
    transferred_amount = fields.Monetary(
        compute="_compute_transferred_amount",
    )

    @api.constrains("active", "state", "analytic_account_id", "budget_period_id")
    def _check_budget_control_unique(self):
        """Not allow multiple active budget control on same period"""
        self.flush()
        query = """
            SELECT analytic_account_id, budget_period_id, COUNT(*)
            FROM budget_control
            WHERE active = TRUE AND state != 'cancel'
                AND analytic_account_id IN %s
                AND budget_period_id IN %s
            GROUP BY analytic_account_id, budget_period_id
        """
        params = (
            tuple(self.mapped("analytic_account_id").ids),
            tuple(self.mapped("budget_period_id").ids),
        )
        self.env.cr.execute(query, params)
        res = self.env.cr.dictfetchall()
        analytic_ids = [x["analytic_account_id"] for x in res if x["count"] > 1]
        if analytic_ids:
            analytics = self.env["account.analytic.account"].browse(analytic_ids)
            raise UserError(
                _("Multiple budget control on the same period for: %s")
                % ", ".join(analytics.mapped("name"))
            )

    @api.depends("analytic_account_id")
    def _compute_initial_balance(self):
        for rec in self:
            rec.amount_initial = (
                rec.analytic_account_id.initial_available
                + rec.analytic_account_id.initial_commit
            )

    @api.constrains("line_ids")
    def _check_budget_control_over_consumed(self):
        BudgetPeriod = self.env["budget.period"]
        if self.env.context.get("edit_amount", False):
            return
        for rec in self.filtered(
            lambda l: l.budget_period_id.control_level == "analytic_kpi"
        ):
            for line in rec.line_ids:
                # Filter according to budget_control parameter
                query, dataset_all = rec.with_context(
                    filter_kpi_ids=[line.kpi_id.id]
                )._get_query_dataset_all()
                # Get data from dataset
                budget_info = BudgetPeriod.get_budget_info_from_dataset(
                    query, dataset_all
                )
                if budget_info["amount_balance"] < 0:
                    raise UserError(
                        _("Total amount in KPI {} will result in {:,.2f}").format(
                            line.name, budget_info["amount_balance"]
                        )
                    )

    @api.onchange("use_all_kpis")
    def _onchange_use_all_kpis(self):
        if self.use_all_kpis:
            self.template_line_ids = self.template_id.line_ids
        else:
            self.template_line_ids = False

    def action_confirm_state(self):
        return {
            "name": _("Confirmation"),
            "type": "ir.actions.act_window",
            "res_model": "budget.state.confirmation",
            "view_mode": "form",
            "target": "new",
            "context": self._context,
        }

    @api.depends("allocated_amount")
    def _compute_allocated_released_amount(self):
        for rec in self:
            rec.released_amount = rec.allocated_amount

    @api.depends("released_amount", "amount_budget")
    def _compute_diff_amount(self):
        for rec in self:
            rec.diff_amount = rec.released_amount - rec.amount_budget

    def _filter_by_budget_control(self, val):
        return (
            val["analytic_account_id"][0] == self.analytic_account_id.id
            and val["budget_period_id"][0] == self.budget_period_id.id
        )

    def _get_domain_dataset_all(self):
        """Retrieve budgeting data for a list of budget_control"""
        analytic_ids = self.mapped("analytic_account_id").ids
        budget_period_ids = self.mapped("budget_period_id").ids
        domain = [
            ("analytic_account_id", "in", analytic_ids),
            ("budget_period_id", "in", budget_period_ids),
        ]
        # Optional filters by context
        if self.env.context.get("no_fwd_commit"):
            domain.append(("fwd_commit", "=", False))
        if self.env.context.get("filter_kpi_ids"):
            domain.append(("kpi_id", "in", self.env.context.get("filter_kpi_ids")))
        return domain

    def _get_context_monitoring(self):
        """Support for add context in monitoring"""
        return self.env.context.copy()

    def _get_query_dataset_all(self):
        BudgetPeriod = self.env["budget.period"]
        MonitorReport = self.env["budget.monitor.report"]
        ctx = self._get_context_monitoring()
        query = BudgetPeriod._budget_info_query()
        domain = self._get_domain_dataset_all()
        dataset_all = MonitorReport.with_context(**ctx).read_group(
            domain=domain,
            fields=query["fields"],
            groupby=query["groupby"],
            lazy=False,
        )
        return query, dataset_all

    def _compute_budget_info(self):
        BudgetPeriod = self.env["budget.period"]
        query, dataset_all = self._get_query_dataset_all()
        for rec in self:
            # Filter according to budget_control parameter
            dataset = [x for x in dataset_all if rec._filter_by_budget_control(x)]
            # Get data from dataset
            budget_info = BudgetPeriod.get_budget_info_from_dataset(query, dataset)
            rec.update(budget_info)

    def _get_lines_init_date(self):
        self.ensure_one()
        init_date = min(self.line_ids.mapped("date_from"))
        return self.line_ids.filtered(lambda l: l.date_from == init_date)

    def do_init_budget_commit(self, init):
        """Initialize budget with current commitment amount."""
        for bc in self:
            bc.update({"init_budget_commit": init})
            if not init or not bc.init_budget_commit or not bc.line_ids:
                continue
            min(bc.line_ids.mapped("date_from"))
            lines = bc._get_lines_init_date()
            for line in lines:
                query_data = bc.budget_period_id._get_budget_avaiable(
                    bc.analytic_account_id.id, line.template_line_id
                )
                # Get init commit amount only
                balance_commit = sum(
                    q["amount"]
                    for q in query_data
                    if q["amount"] is not None
                    and q["amount_type"] not in ["1_budget", "8_actual"]
                )
                line.update({"amount": abs(balance_commit)})

    @api.onchange("init_budget_commit")
    def _onchange_init_budget_commit(self):
        self.do_init_budget_commit(self.init_budget_commit)

    def _check_budget_amount(self):
        for rec in self:
            # Check plan vs released
            if (
                float_compare(
                    rec.amount_budget,
                    rec.released_amount,
                    precision_rounding=rec.currency_id.rounding,
                )
                != 0
            ):
                raise UserError(
                    _(
                        "Planning amount should equal to the released amount {:,.2f} {}"
                    ).format(rec.released_amount, rec.currency_id.symbol)
                )
            # Check plan vs intial
            if (
                float_compare(
                    rec.amount_initial,
                    rec.amount_budget,
                    precision_rounding=rec.currency_id.rounding,
                )
                == 1
            ):
                raise UserError(
                    _(
                        "Planning amount should be greater than "
                        "initial balance {:,.2f} {}"
                    ).format(rec.amount_initial, rec.currency_id.symbol)
                )

    def action_draft(self):
        return self.write({"state": "draft"})

    def action_submit(self):
        self._check_budget_amount()
        return self.write({"state": "submit"})

    def action_done(self):
        self._check_budget_amount()
        return self.write({"state": "done"})

    def action_cancel(self):
        return self.write({"state": "cancel"})

    def _domain_template_line(self):
        return [("id", "in", self.template_line_ids.ids)]

    def _get_dict_budget_lines(self, date_range, template_line):
        return {
            "template_line_id": template_line.id,
            "date_range_id": date_range.id,
            "date_from": date_range.date_start,
            "date_to": date_range.date_end,
            "analytic_account_id": self.analytic_account_id.id,
            "budget_control_id": self.id,
        }

    def _get_budget_lines(self, date_range, template_line):
        self.ensure_one()
        dict_value = self._get_dict_budget_lines(date_range, template_line)
        if self._context.get("keep_item_amount", False):
            # convert dict to list
            domain_item = [(k, "=", v) for k, v in dict_value.items()]
            item = self.line_ids.search(domain_item, limit=1)
            dict_value["amount"] = item.amount
        return dict_value

    def _keep_item_amount(self, vals, old_items):
        """Find amount from old plan for update new plan"""
        for val in vals:
            domain_item = [(k, "=", v) for k, v in val.items()]
            item = old_items.search(domain_item)
            val["amount"] = item.amount

    def prepare_budget_control_matrix(self):
        BudgetTemplateLine = self.env["budget.template.line"]
        DateRange = self.env["date.range"]
        for bc in self:
            if not bc.plan_date_range_type_id:
                raise UserError(_("Please select range"))
            template_lines = BudgetTemplateLine.search(bc._domain_template_line())
            date_ranges = DateRange.search(
                [
                    ("type_id", "=", bc.plan_date_range_type_id.id),
                    ("date_start", ">=", bc.date_from),
                    ("date_end", "<=", bc.date_to),
                ]
            )
            items = []
            for date_range in date_ranges:
                items += [
                    bc._get_budget_lines(date_range, template_line)
                    for template_line in template_lines
                ]
            # Delete the existing budget lines
            bc.line_ids.unlink()
            # Create the new budget lines and Reset the carry over budget
            bc.write(
                {
                    "init_budget_commit": False,
                    "line_ids": [(0, 0, val) for val in items],
                }
            )

    def _get_domain_budget_monitoring(self):
        return [("analytic_account_id", "=", self.analytic_account_id.id)]

    def _get_context_budget_monitoring(self):
        ctx = {"search_default_group_by_analytic_account": 1}
        return ctx

    def action_view_monitoring(self):
        self.ensure_one()
        ctx = self._get_context_budget_monitoring()
        domain = self._get_domain_budget_monitoring()
        return {
            "name": _("Budget Monitoring"),
            "res_model": "budget.monitor.report",
            "view_mode": "pivot,tree,graph",
            "domain": domain,
            "context": ctx,
            "type": "ir.actions.act_window",
        }

    def _get_domain_transfer_item_ids(self):
        self.ensure_one()
        return [
            ("state", "=", "transfer"),
            "|",
            ("budget_control_from_id", "=", self.id),
            ("budget_control_to_id", "=", self.id),
        ]

    def _compute_transfer_item_ids(self):
        TransferItem = self.env["budget.transfer.item"]
        for rec in self:
            items = TransferItem.search(rec._get_domain_transfer_item_ids())
            rec.transfer_item_ids = items

    @api.depends("transfer_item_ids")
    def _compute_transferred_amount(self):
        for rec in self:
            # Get the transfer items where the current budget control is the source
            from_transfer_items = rec.transfer_item_ids.filtered(
                lambda l: l.budget_control_from_id == rec
            )
            # Get the transfer items where the current budget control is the destination
            to_transfer_items = rec.transfer_item_ids - from_transfer_items
            # Calculate the total transferred amount by subtracting the amount transferred
            total_amount = sum(to_transfer_items.mapped("amount")) - sum(
                from_transfer_items.mapped("amount")
            )
            rec.transferred_amount = total_amount

    def action_open_budget_transfer_item(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({"create": False, "edit": False})
        items = self.transfer_item_ids
        list_view = self.env.ref("budget_control.view_budget_transfer_item_ref_tree").id
        form_view = self.env.ref("budget_control.view_budget_transfer_item_ref_form").id
        return {
            "name": _("Budget Transfer Items"),
            "type": "ir.actions.act_window",
            "res_model": "budget.transfer.item",
            "views": [[list_view, "list"], [form_view, "form"]],
            "view_mode": "list",
            "context": ctx,
            "domain": [("id", "in", items and items.ids or [])],
        }


class BudgetControlLine(models.Model):
    _name = "budget.control.line"
    _description = "Budget Control Lines"
    _order = "date_range_id, kpi_id"

    budget_control_id = fields.Many2one(
        comodel_name="budget.control",
        ondelete="cascade",
        index=True,
        required=True,
    )
    name = fields.Char(compute="_compute_name", required=False, readonly=True)
    date_range_id = fields.Many2one(
        comodel_name="date.range",
        string="Date range",
    )
    date_from = fields.Date(required=True, string="From")
    date_to = fields.Date(required=True, string="To")
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account", string="Analytic account"
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag", string="Analytic Tags"
    )
    amount = fields.Float()
    template_line_id = fields.Many2one(
        comodel_name="budget.template.line",
        index=True,
    )
    kpi_id = fields.Many2one(
        comodel_name="budget.kpi",
        related="template_line_id.kpi_id",
        store=True,
    )
    active = fields.Boolean(
        compute="_compute_active",
        readonly=True,
        store=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submit", "Submitted"),
            ("done", "Controlled"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        compute="_compute_budget_control_state",
        store=True,
        index=True,
    )

    @api.depends("kpi_id")
    def _compute_name(self):
        for rec in self:
            rec.name = rec.kpi_id.display_name

    @api.depends("budget_control_id.state")
    def _compute_budget_control_state(self):
        for rec in self:
            rec.state = rec.budget_control_id.state

    @api.depends("budget_control_id.active")
    def _compute_active(self):
        for rec in self:
            rec.active = rec.budget_control_id.active if rec.budget_control_id else True
