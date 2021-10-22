# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from operator import itemgetter

from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_compare, format_amount


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
        index=True,
        help="Automatically created report instance for this budget period",
    )
    mis_budget_id = fields.Many2one(
        comodel_name="mis.budget",
        string="MIS Budget",
        readonly=True,
        ondelete="restrict",
        index=True,
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
        selection=[
            ("analytic", "Analytic"),
            ("analytic_kpi", "Analytic & KPI"),
        ],
        string="Level of Control",
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
    # include_tax = fields.Boolean(string="Included Tax")
    analytic_line = fields.One2many(
        comodel_name="account.analytic.account",
        inverse_name="budget_period_id",
    )

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        res["report_id"] = self.env.company.budget_kpi_template_id.id
        return res

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
        if "report_id" in vals:
            mis_budgets = self.mapped("mis_budget_id")
            mis_budgets.write({"report_id": vals["report_id"]})
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

    def _check_budget_period_date_range(self):
        self.ensure_one()
        range_from = self.env["date.range"].search(
            [
                ("date_start", "<=", self.bm_date_from),
                ("date_end", ">=", self.bm_date_from),
            ]
        )
        range_to = self.env["date.range"].search(
            [
                ("date_start", "<=", self.bm_date_to),
                ("date_end", ">=", self.bm_date_to),
            ]
        )
        if not range_from or not range_to:
            action = self.env.ref("date_range.date_range_generator_action")
            msg = (
                _(
                    "There are no date ranges for the budget period, %s, yet.\n"
                    "Please create date ranges that will cover this budget period."
                )
                % self.display_name
            )
            raise RedirectWarning(msg, action.id, _("Generate date range now"))

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
        actual_model = self.env.ref("budget_control.model_account_budget_move")
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
                "source": "actuals_alt",
                "source_aml_model_id": actual_model.id,
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
    def check_budget(self, doclines, doc_type="account"):
        """Based in input budget_moves, i.e., account_move_line
        1. Get a valid budget.period (how budget is being controlled)
        2. (1) and doclines, determine what account(kpi)+analytic to ctrl
        3. Prepare kpis (kpi by account_id)
        4. Get report instance as created by budget.period
        5. (2) + (3) + (4) -> kpi_matrix -> negative budget -> warnings
        """
        if self._context.get("force_no_budget_check"):
            return
        doclines = doclines.filtered("can_commit")
        if not doclines:
            return
        self = self.sudo()
        # Find active budget.period based on latest doclines date_commit
        date_commit = doclines.filtered("date_commit").mapped("date_commit")
        if not date_commit:
            return
        date_commit = max(date_commit)
        budget_period = self._get_eligible_budget_period(date_commit, doc_type=doc_type)
        if not budget_period:
            return
        # Find combination of account(kpi) + analytic(i.e.,project) to control
        controls = self._prepare_controls(budget_period, doclines)
        if not controls:
            return
        # The budget_control of these analytics must active
        analytic_ids = [x["analytic_id"] for x in controls]
        analytics = self.env["account.analytic.account"].browse(analytic_ids)
        analytics._check_budget_control_status(budget_period_id=budget_period.id)
        # Prepare kpis by account_id
        instance = budget_period.report_instance_id
        company = self.env.user.company_id
        kpis = instance.report_id.get_kpis(company)
        # Check budget on each control elements against each kpi/avail(period)
        currency = (
            "currency_id" in doclines
            and doclines.mapped("currency_id")[:1]
            or self.env.context.get("doc_currency", False)
        )
        warnings = self.with_context(
            date_commit=date_commit, doc_currency=currency
        )._check_budget_available(instance, controls, kpis)
        if warnings:
            msg = "\n".join([_("Budget not sufficient,"), "\n".join(warnings)])
            raise UserError(msg)
        return

    @api.model
    def check_budget_precommit(self, doclines, doc_type="account"):
        """Precommit check,
        first do the normal commit, do checking, and remove commits"""
        if not doclines:
            return
        # Commit budget
        budget_moves = []
        for line in doclines:
            budget_move = line.with_context(force_commit=True).commit_budget()
            if budget_move:
                budget_moves.append(budget_move)
        # Check Budget
        self.env["budget.period"].check_budget(doclines, doc_type=doc_type)
        # Remove commits
        for budget_move in budget_moves:
            budget_move.unlink()

    @api.model
    def check_over_returned_budget(self, docline, reverse=False):
        self = self.sudo()
        doc = docline[docline._doc_rel]
        budget_moves = doc[docline._budget_field()]
        credit = sum(budget_moves.mapped("credit"))
        debit = sum(budget_moves.mapped("debit"))
        amount_credit = reverse and debit or credit
        amount_debit = reverse and credit or debit
        # For now, when any over returned budget, make immediate adjustment
        if float_compare(amount_credit, amount_debit, 2) == 1:
            docline.with_context(
                use_amount_commit=True,
                commit_note=_("Over returned auto adjustment, %s")
                % docline.display_name,
            ).commit_budget(reverse=True)

    @api.model
    def _get_eligible_budget_period(self, date=False, doc_type=False):
        if not date:
            date = fields.Date.context_today(self)
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
        if doc_type:
            return budget_period.filtered(doc_type)  # Only if to control
        else:
            return budget_period

    @api.model
    def _prepare_controls(self, budget_period, doclines):
        controls = set()
        control_analytics = budget_period.control_analytic_account_ids
        budget_moves = doclines.mapped(doclines._budget_field())
        for i in budget_moves:
            if budget_period.control_all_analytic_accounts:
                if i.analytic_account_id and i.account_id:
                    controls.add((i.analytic_account_id.id, i.account_id.id))
            else:  # Only analtyic in control
                if i.analytic_account_id in control_analytics and i.account_id:
                    controls.add((i.analytic_account_id.id, i.account_id.id))
        # Convert to list of dict, for readibility
        return [{"analytic_id": x[0], "account_id": x[1]} for x in controls]

    @api.model
    def _prepare_matrix_by_analytic(self, instance, analytic_ids):
        """Return resulting matrix based on each analytic."""
        ctx = self._context.copy()
        matrix = {}
        for analytic_id in analytic_ids:
            if not matrix.get(analytic_id):
                ctx.update({"filter_analytic_ids": [analytic_id]})
                kpi_matrix = instance.with_context(ctx)._compute_matrix()
                matrix[analytic_id] = kpi_matrix
        return matrix

    @api.model
    def _prepare_matrix_all_analytics(self, instance, analytic_ids):
        """Return resulting matrix of all analytic combined."""
        ctx = self._context.copy()
        ctx.update({"filter_analytic_ids": analytic_ids})
        return instance.with_context(ctx)._compute_matrix()

    @api.model
    def _get_kpi_value(self, kpi_matrix, kpi, period):
        period.ensure_one()
        for row in kpi_matrix.iter_rows():
            if row.kpi == kpi:
                for cell in row.iter_cells():
                    if cell.subcol.col.key == period.id:
                        return cell.val or 0.0
        return 0.0

    @api.model
    def _get_kpis_value(self, kpi_matrix, kpi_lines, period):
        period.ensure_one()
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
    def _get_kpi_by_control_key(self, instance, kpis, control):
        """
        By default, control key is account_id as it can be used to get KPI
        In future, this can be other key, i.e., activity_id based on installed module
        """
        account_id = control["account_id"]
        kpi = kpis.get(account_id, [])
        if len(kpi) == 1:
            return kpi
        # Invalid KPI
        account = self.env["account.account"].browse(account_id)
        if not kpi:
            raise UserError(
                _("Chosen account code %s is not valid for budgeting")
                % account.display_name
            )
        else:
            raise UserError(
                _(
                    "KPI Template '%s' has more than one KPI being "
                    "refereced by same account code %s"
                )
                % (instance.report_id.name, account.display_name)
            )
        return kpi

    @api.model
    def _check_budget_available(self, instance, controls, kpis):
        """
        This function is a CORE function, please modify carefully
        Author: Kitti U.
        """
        warnings = []
        Analytic = self.env["account.analytic.account"]
        BudgetPeriod = self.env["budget.period"]
        # Prepare result matrix for all analytic_id to be tested
        analytic_ids = [x["analytic_id"] for x in controls]
        kpi_matrix = self._prepare_matrix_by_analytic(instance, analytic_ids)
        # Find period that determine budget amount balance (sumcol)
        balance_period = instance.period_ids.filtered_domain(
            [("source", "=", "sumcol")]
        )
        for control in controls:
            analytic_id = control["analytic_id"]
            # Get kpi to check budget, for case control_level = analytic_kpi
            kpi = self._get_kpi_by_control_key(instance, kpis, control)
            # Check control_level in Budget, aka, analtyic, analytic_kpi
            budget_period = BudgetPeriod.search(
                [("report_instance_id", "=", instance.id)]
            )
            balance = False
            if budget_period.control_level == "analytic":
                kpi_lines = {list(kpis.get(x))[0] for x in kpis}
                balance = self._get_kpis_value(
                    kpi_matrix[analytic_id], kpi_lines, balance_period
                )
            else:
                balance = self._get_kpi_value(
                    kpi_matrix[analytic_id], list(kpi)[0], balance_period
                )
            # Show warning if budget not enough
            if balance < 0:
                # Convert to document currency
                company = self.env.user.company_id
                doc_currency = self.env.context.get("doc_currency")
                date_commit = self.env.context.get("date_commit")
                balance_currency = company.currency_id._convert(
                    balance, doc_currency, company, date_commit
                )
                fomatted_balance = format_amount(
                    self.env, balance_currency, doc_currency
                )
                analytic_name = Analytic.browse(analytic_id).display_name
                if budget_period.control_level == "analytic":
                    warnings.append(
                        _("{0}, will result in {1}").format(
                            analytic_name, fomatted_balance
                        )
                    )
                else:
                    kpi_name = list(kpi)[0].display_name
                    warnings.append(
                        _("{0} & {1}, will result in {2}").format(
                            kpi_name, analytic_name, fomatted_balance
                        )
                    )
        return list(set(warnings))

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
            [
                ("name", "in", col_names),
                ("report_instance_id", "=", instance.id),
            ]
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

    def get_budget_info(self, analytic_ids):
        """Get budget overview by analytics, return as dict, i.e.,
        budget_info = {
            "amount_budget": 100,
            "amount_actual": 70,
            "amount_balance": 30
        }
        Note: based on installed modules
        """
        self.ensure_one()
        budget_info = {
            "amount_budget": 0,
            "amount_commit": 0,
            "amount_actual": 0,
            "amount_consumed": 0,
            "amount_balance": 0,
        }
        company = self.env.user.company_id
        instance = self.report_instance_id
        kpis = instance.report_id.get_kpis(company)
        kpi_lines = {list(kpis.get(x))[0] for x in kpis}
        kpi_matrix = self._prepare_matrix_all_analytics(instance, analytic_ids)
        self._compute_budget_info(
            kpi_matrix=kpi_matrix, kpi_lines=kpi_lines, budget_info=budget_info
        )
        return budget_info

    def _set_budget_info_amount(self, source, domain, kwargs, is_commit=False):
        self.ensure_one()
        kpi_matrix, kpi_lines, info = itemgetter(
            "kpi_matrix", "kpi_lines", "budget_info"
        )(kwargs)
        period = self.period_ids.filtered_domain(domain)
        if not period:
            info[source] = 0
            return
        amount = self.env["budget.period"]._get_kpis_value(
            kpi_matrix, kpi_lines, period
        )
        info[source] = amount
        if is_commit:
            info["amount_commit"] += amount
        info["amount_consumed"] = info["amount_commit"] + info["amount_actual"]

    def _compute_budget_info(self, **kwargs):
        """ Add more data info budget_info, based on installed modules """
        self.ensure_one()
        self._set_budget_info_amount(
            "amount_budget", [("source", "=", "mis_budget")], kwargs
        )
        self._set_budget_info_amount(
            "amount_actual",
            [("source_aml_model_id.model", "=", "account.budget.move")],
            kwargs,
        )
        self._set_budget_info_amount(
            "amount_balance", [("source", "=", "sumcol")], kwargs
        )

    @api.model
    def get_budget_info_from_dataset(self, query, dataset):
        """Get budget overview from a budget monitor dataset, i.e.,
        budget_info = {
            "amount_budget": 100,
            "amount_actual": 70,
            "amount_balance": 30
        }
        Note: based on installed modules
        """
        budget_info = {col: 0 for col in query["info_cols"].keys()}
        budget_info["amount_commit"] = 0
        for col, (amount_type, is_commit) in query["info_cols"].items():
            info = list(filter(lambda l: l["amount_type"] == amount_type, dataset))
            if len(info) > 1:
                raise ValidationError(_("Error retrieving budget info!"))
            if info:
                if is_commit:
                    budget_info[col] = -info[0]["amount"]  # Negate
                    budget_info["amount_commit"] += budget_info[col]
                    continue
                if amount_type == "8_actual":  # Negate consumed
                    budget_info[col] = -info[0]["amount"]
                    continue
                budget_info[col] = info[0]["amount"]
        budget_info["amount_consumed"] = (
            budget_info["amount_commit"] + budget_info["amount_actual"]
        )
        budget_info["amount_balance"] = (
            budget_info["amount_budget"] - budget_info["amount_consumed"]
        )
        return budget_info

    def _budget_info_query(self):
        query = {
            "info_cols": {
                "amount_budget": (
                    "1_budget",
                    False,
                ),  # (amount_type, is_commit)
                "amount_actual": ("8_actual", False),
            },
            "fields": [
                "analytic_account_id",
                "budget_period_id",
                "amount_type",
                "amount",
            ],
            "groupby": [
                "analytic_account_id",
                "budget_period_id",
                "amount_type",
            ],
        }
        return query
