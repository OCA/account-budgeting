# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class BudgetPeriod(models.Model):
    _name = "budget.period"
    _inherits = {"mis.report.instance": "report_instance_id"}
    _description = "For each fiscal year, manage how budget is controlled"

    report_instance_id = fields.Many2one(
        comodel_name="mis.report.instance",
        string="Budget MIS Instance",
        readonly=False,
        ondelete="restrict",
        required=True,
        help="Automatically created report instance for this budget period",
    )
    mis_budget_id = fields.Many2one(
        comodel_name="mis.budget",
        string="MIS Budget",
        readonly=True,
        ondelete="restrict",
        help="Automatically created mis budget",
    )
    bm_date_from = fields.Date(
        string="Date From",
        required=True,
    )
    bm_date_to = fields.Date(
        string="Date To",
        required=True,
    )
    account = fields.Boolean(
        string="On Account",
        default=False,
        help="Control budget on journal document(s), i.e., vendor bill",
    )
    control_all_analytic_accounts = fields.Boolean(
        string="Control All Analytics",
        default=True,
    )
    control_analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        relation="budget_period_analytic_account_rel",
        string="Controlled Analytics",
    )
    control_level = fields.Selection(
        selection=[("analytic", "Analytic"), ("analytic_kpi", "Analytic & KPI")],
        string="Level of Control (TBD)",
        required=True,
        default="analytic",
        help="Level of budget check.\n"
        "1. Based on Analytic Account only\n"
        "2. Based on Analytic Account & KPI (more fine granied)",
    )
    plan_date_range_type_id = fields.Many2one(
        comodel_name="date.range.type",
        string="Plan Date Range",
        required=True,
        help="Budget control sheet in this budget control year, will use this "
        "data range to plan the budget.",
    )

    @api.model
    def create(self, vals):
        # Auto create mis.budget, and link it to same kpi and date range
        mis_budget = self.env["mis.budget"].create(
            {
                "name": _("%s - Budget") % vals["name"],
                "report_id": vals["report_id"],
                "date_from": vals["bm_date_from"],
                "date_to": vals["bm_date_to"],
            }
        )
        vals.update(
            {
                "comparison_mode": True,
                "target_move": "posted",
                "mis_budget_id": mis_budget.id,
            }
        )
        budget_period = super().create(vals)
        budget_period._recompute_report_instance_periods()
        return budget_period

    def write(self, vals):
        vals.update({"comparison_mode": True, "target_move": "posted"})
        res = super().write(vals)
        self._recompute_report_instance_periods()
        return res

    def unlink(self):
        report_instances = self.mapped("report_instance_id")
        mis_budgets = self.mapped("mis_budget_id")
        res = super().unlink()
        report_instances.mapped("period_ids.source_sumcol_ids").unlink()
        report_instances.mapped("period_ids").unlink()
        report_instances.unlink()
        mis_budgets.unlink()
        return res

    def action_view_budget_control(self):
        """View all budget.control sharing same mis_budget_id."""
        self.ensure_one()
        action = self.env.ref("budget_control.budget_control_action")
        res = action.read()[0]
        budget_controls = self.env["budget.control"].search(
            [("budget_id", "=", self.mis_budget_id.id)]
        )
        res.update({"domain": [("id", "in", budget_controls.ids)]})
        return res

    def _recompute_report_instance_periods(self):
        for budget_period in self:
            budget_period.report_instance_id.period_ids.mapped(
                "source_sumcol_ids"
            ).unlink()
            budget_period.report_instance_id.period_ids.unlink()
            budget_period._create_report_instance_period()

    def _create_budget_move_periods(self):
        self.ensure_one()
        Period = self.env["mis.report.instance.period"]
        periods = {}
        budget = Period.create(
            {
                "name": "Budgeted",
                "report_instance_id": self.report_instance_id.id,
                "sequence": 10,
                "source": "mis_budget",
                "source_mis_budget_id": self.mis_budget_id.id,
                "mode": "fix",
                "manual_date_from": self.bm_date_from,
                "manual_date_to": self.bm_date_to,
            }
        )
        actual = Period.create(
            {
                "name": "Actuals",
                "report_instance_id": self.report_instance_id.id,
                "sequence": 90,
                "source": "actuals",
                "mode": "fix",
                "manual_date_from": self.bm_date_from,
                "manual_date_to": self.bm_date_to,
            }
        )
        periods = {budget: "+", actual: "-"}
        return periods

    def _create_report_instance_period(self):
        self.ensure_one()
        Period = self.env["mis.report.instance.period"]
        periods = self._create_budget_move_periods()
        sumcols_list = []
        for period, sign in periods.items():
            sumcols_list.append((0, 0, {"sign": sign, "period_to_sum_id": period.id}))
        Period.create(
            {
                "name": "Available",
                "report_instance_id": self.report_instance_id.id,
                "sequence": 100,
                "source": "sumcol",
                "source_sumcol_ids": sumcols_list,
                "mode": "none",
            }
        )

    @api.model
    def check_budget(self, budget_moves, doc_type="account"):
        """Based in input budget_moves, i.e., account_move_line
        1. Get a valid budget.period (how budget is being controlled)
        2. (1) and budget_moves, determine what account(kpi)+analytic to ctrl
        3. Prepare kpis (kpi by account_id)
        4. Get report instance as created by budget.period
        5. (2) + (3) + (4) -> kpi_matrix -> negative budget -> warnings
        """
        if self._context.get("force_no_budget_check"):
            return
        if not budget_moves:
            return
        self = self.sudo()
        # Find active budget.period based on budget_moves date
        date = set(budget_moves.mapped("date"))
        if len(date) != 1:
            raise ValidationError(_("Budget moves' date not unified"))
        budget_period = self._get_eligible_budget_period(date.pop(), doc_type)
        if not budget_period:
            return
        # Find combination of account(kpi) + analytic(i.e.,project) to control
        controls = self._prepare_controls(budget_period, budget_moves)
        if not controls:
            return
        # Prepare kpis by account_id
        instance = budget_period.report_instance_id
        company = self.env.user.company_id
        kpis = instance.report_id.get_kpis_by_account_id(company)
        if not kpis:
            return
        # Check budget on each control elements against each kpi/avail(period)
        warnings = self._check_budget_available(instance, controls, kpis)
        if warnings:
            msg = "\n".join([_("Budget not sufficient,"), "\n".join(warnings)])
            raise UserError(msg)
        return

    @api.model
    def check_over_returned_budget(self, doc, reverse=False):
        self = self.sudo()
        credit = sum(doc.budget_move_ids.mapped("credit"))
        debit = sum(doc.budget_move_ids.mapped("debit"))
        amount_credit = reverse and debit or credit
        amount_debit = reverse and credit or debit
        if float_compare(amount_credit, amount_debit, 2) == 1:
            raise ValidationError(
                _("This operation will result in over returned budget on %s")
                % doc.display_name
            )

    @api.model
    def _get_eligible_budget_period(self, date, doc_type):
        BudgetPeriod = self.env["budget.period"]
        budget_period = BudgetPeriod.search(
            [("bm_date_from", "<=", date), ("bm_date_to", ">=", date)]
        )
        if budget_period and len(budget_period) > 1:
            raise ValidationError(
                _(
                    "Multiple Budget Period found for date %s.\nPlease "
                    "ensure one Budget Period valid for this date"
                )
                % date
            )
        return budget_period.filtered(doc_type)  # Only if to control

    @api.model
    def _prepare_controls(self, budget_period, budget_moves):
        controls = set()
        control_analytics = budget_period.control_analytic_account_ids
        for i in budget_moves:
            if budget_period.control_all_analytic_accounts:
                if i.analytic_account_id and i.account_id:
                    controls.add((i.analytic_account_id.id, i.account_id.id))
            else:  # Only analtyic in control
                if i.analytic_account_id in control_analytics and i.account_id:
                    controls.add((i.analytic_account_id.id, i.account_id.id))
        return controls

    @api.model
    def _prepare_matrix_by_analytic(self, instance, analytic_ids):
        """Return resulting matrix based on each analytic."""
        matrix = {}
        for analytic_id in analytic_ids:
            if not matrix.get(analytic_id):
                analytic_filter = {
                    "analytic_account_id": {
                        "value": analytic_id,
                        "operator": "=",
                    }
                }
                ctx = {"mis_report_filters": analytic_filter}
                matrix[analytic_id] = instance.with_context(ctx)._compute_matrix()
        return matrix

    @api.model
    def _get_kpi_value(self, kpi_matrix, kpi, period):
        for row in kpi_matrix.iter_rows():
            if row.kpi == kpi:
                for cell in row.iter_cells():
                    if cell.subcol.col.key == period.id:
                        return cell.val or 0.0
        return 0.0

    @api.model
    def _get_kpis_value(self, kpi_matrix, kpi_lines, period):
        value = 0.0
        details_kpi = False
        for row in kpi_matrix.iter_rows():
            if row.kpi in kpi_lines and row.kpi != details_kpi:
                for cell in row.iter_cells():
                    if cell.subcol.col.key == period.id:
                        value += cell.val
            details_kpi = row.kpi
        return value

    @api.model
    def _check_budget_available(self, instance, controls, kpis):
        warnings = []
        Account = self.env["account.account"]
        Analytic = self.env["account.analytic.account"]
        BudgetPeriod = self.env["budget.period"]
        # Prepare result matrix for all analytic_id to be tested
        analytic_ids = [x[0] for x in list(controls)]
        kpi_matrix = self._prepare_matrix_by_analytic(instance, analytic_ids)
        # Find period that determine budget amount available (sumcol)
        period = instance.period_ids.filtered(lambda l: l.source == "sumcol")
        period.ensure_one()  # Test to ensure one
        for analytic_id, account_id in controls:
            kpi = kpis.get(account_id, False)
            if not kpi:
                continue
            if len(kpi) != 1:
                account = Account.browse(account_id)
                raise UserError(
                    _(
                        'KPI Template "%s" has more than one KPI being '
                        "refereced by same account code %s"
                    )
                    % (instance.report_id.name, account.code)
                )

            # Checl Level of Control in Budget
            budget_period = BudgetPeriod.search(
                [("report_instance_id", "=", instance.id)]
            )
            if budget_period.control_level == "analytic":
                kpi_lines = {list(kpis.get(x))[0] for x in kpis}
                amount = self._get_kpis_value(
                    kpi_matrix[analytic_id], kpi_lines, period
                )
            else:
                amount = self._get_kpi_value(
                    kpi_matrix[analytic_id], list(kpi)[0], period
                )
            if amount < 0:
                analytic = Analytic.browse(analytic_id).display_name
                kpi_name = list(kpi)[0].display_name
                warnings.append(
                    _("{0} on {1}, will result in {2:,.2f}").format(
                        kpi_name, analytic, amount
                    )
                )
        return warnings

    def get_report_amount(self, kpi_names=None, col_names=None, analytic_id=False):
        self.ensure_one()
        return self._get_amount(
            self.report_instance_id.id,
            kpi_names=kpi_names,
            col_names=col_names,
            analytic_id=analytic_id,
        )

    @api.model
    def _get_amount(
        self, instance_id, kpi_names=None, col_names=None, analytic_id=False
    ):
        instance = self.env["mis.report.instance"].browse(instance_id)
        report = instance.report_id
        kpis = self.env["mis.report.kpi"].search(
            [("name", "in", kpi_names), ("report_id", "=", report.id)]
        )
        periods = self.env["mis.report.instance.period"].search(
            [("name", "in", col_names), ("report_instance_id", "=", instance.id)]
        )
        ctx = {}
        if analytic_id:
            ctx = {
                "mis_report_filters": {
                    "analytic_account_id": {
                        "value": analytic_id,
                        "operator": "=",
                    }
                }
            }
        kpi_matrix = instance.with_context(ctx)._compute_matrix()
        amount = 0.0
        for kpi in kpis:
            for period in periods:
                amount += self._get_kpi_value(kpi_matrix, kpi, period)
        return amount

    def budget_preview(self):
        # Redirect to report_instance_id
        return self.report_instance_id.preview()

    def budget_print_pdf(self):
        # Redirect to report_instance_id
        return self.report_instance_id.print_pdf()

    def budget_export_xls(self):
        # Redirect to report_instance_id
        return self.report_instance_id.export_xls()
