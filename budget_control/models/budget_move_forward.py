# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

METHOD_TYPE = [("new", "New Analytic"), ("extend", "Extend")]


class BudgetMoveForward(models.Model):
    _name = "budget.move.forward"
    _description = "Budget Move Forward"
    _inherit = ["mail.thread"]

    name = fields.Char(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
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
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )
    budget_period_id = fields.Many2one(
        comodel_name="budget.period",
        string="From Budget Period",
        default=lambda self: self._get_budget_period(),
        required=True,
    )
    to_budget_id = fields.Many2one(
        comodel_name="mis.budget",
        string="To Budget Period",
        required=True,
        ondelete="restrict",
        readonly=True,
        states={"draft": [("readonly", False)]},
        # TODO: add domain, and default
    )
    date_from = fields.Date(
        related="to_budget_id.date_from",
        string="Move to date",
    )
    date_to = fields.Date(related="to_budget_id.date_to")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        default="draft",
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency", related="company_id.currency_id"
    )
    method_type = fields.Selection(
        METHOD_TYPE,
        string="Method",
        default="new",
        required=True,
    )
    accumulate_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Accumulated Analytic Account",
    )
    date_extend = fields.Date(
        string="Extended Date",
        related="to_budget_id.date_to",
        store=True,
    )
    forward_line_ids = fields.One2many(
        comodel_name="budget.move.forward.line",
        inverse_name="forward_id",
        string="Forward Lines",
        readonly=True,
    )
    forward_accumulate_ids = fields.One2many(
        comodel_name="budget.move.forward.line.accumulate",
        inverse_name="forward_id",
        string="Accumulate Lines",
    )
    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "Name must be unique!"),
    ]

    @api.onchange("method_type")
    def _onchange_method_type(self):
        self.forward_accumulate_ids._onchange_reset_method_type()

    @api.constrains("to_budget_id", "state")
    def check_to_budget_already(self):
        """ Carry Forward can do 1 time / budget period """
        MoveForward = self.env["budget.move.forward"]
        for rec in self:
            forward_id = MoveForward.search(
                [
                    ("to_budget_id", "=", rec.to_budget_id.id),
                    ("state", "=", "done"),
                ]
            )
            if len(forward_id) > 1:
                raise UserError(
                    _("{} carry forward already.".format(rec.to_budget_id.name))
                )

    @api.model
    def _get_budget_period(self):
        budget_period = self.env["budget.period"]._get_eligible_budget_period()
        return budget_period

    def _get_domain_search(self, model):
        self.ensure_one()
        domain_search = [
            ("amount_commit", ">", 0.0),
            ("date_commit", "<", self.date_from),
        ]
        return domain_search

    def _get_domain_unlink(self, model):
        self.ensure_one()
        domain_search = [
            ("forward_id", "=", self.id),
            ("res_model", "=", model),
        ]
        return domain_search

    def _get_document_number(self, doc):
        return False

    def _prepare_vals_forward(self, docs, model):
        self.ensure_one()
        value_dict = []
        for doc in docs:
            # Filter out budget move that have been carry forward.
            analytic = doc[doc._budget_analytic_field]
            current_move = doc._filter_current_move(analytic)
            current_commit_move = sum(current_move.mapped("debit")) - sum(
                current_move.mapped("credit")
            )
            if not current_commit_move:
                continue
            analytic_account = doc[doc._budget_analytic_field]
            value_dict.append(
                {
                    "forward_id": self.id,
                    "analytic_account_id": analytic_account.id,
                    "method_type": self.method_type,
                    "res_model": model,
                    "res_id": doc.id,
                    "document_id": "{},{}".format(model, doc.id),
                    "document_number": self._get_document_number(doc),
                    "amount_commit": doc.amount_commit,
                    "date_commit": doc.date_commit,
                }
            )
        return value_dict

    def get_budget_move_forward(self):
        """Get budget move forward for each new commit document type."""
        Line = self.env["budget.move.forward.line"]
        specific_model = self._context.get("res_model", False)
        # Add permission admin to budget team
        self = self.sudo()
        for rec in self:
            models = Line._fields["res_model"].selection
            for model in list(dict(models).keys()):
                if specific_model and specific_model != model:
                    continue
                domain_unlink = rec._get_domain_unlink(model)
                Line.search(domain_unlink).unlink()
                domain_search = rec._get_domain_search(model)
                docs = self.env[model].search(domain_search)
                vals = rec._prepare_vals_forward(docs, model)
                Line.create(vals)

    def _prepare_vals_forward_accumulate(self, analytic):
        self.ensure_one()
        return {
            "forward_id": self.id,
            "analytic_account_id": analytic.id,
            "method_type": self.method_type,
            "amount_balance": analytic.amount_balance,
            "amount_carry_forward": 0.0,
            "amount_accumulate": analytic.amount_balance,
        }

    def _get_domain_prepare_new_analytic(self):
        return [("forward_id", "in", self.ids)]

    def action_prepare_new_analytic(self):
        BudgetForwardLine = self.env["budget.move.forward.line"]
        domain = self._get_domain_prepare_new_analytic()
        forward_line = BudgetForwardLine.search(domain)
        forward_line._prepare_new_analytic()
        for rec in self:
            rec.forward_accumulate_ids._prepare_new_analytic()

    def action_get_analytic_available(self):
        Line = self.env["budget.move.forward.line.accumulate"]
        AnalyticAccount = self.env["account.analytic.account"]
        # Add permission admin to budget team
        self = self.sudo()
        for rec in self:
            rec.forward_accumulate_ids.unlink()
            analytics = AnalyticAccount.search(
                [
                    ("budget_period_id", "=", rec.budget_period_id.id),
                ]
            )
            analytics_available = analytics.filtered(lambda l: l.amount_balance > 0.0)
            vals = [
                rec._prepare_vals_forward_accumulate(analytic)
                for analytic in analytics_available
            ]
            Line.create(vals)

    def carry_forward_accumulate(self, accumulate_lines):
        self.ensure_one()
        for line in accumulate_lines:
            line._check_constraint_analytic()
            if line.method_type == "extend":
                line.analytic_account_id.write(
                    {
                        "bm_date_to": line.date_extend,
                        "initial_available": line.amount_carry_forward,
                    }
                )
            elif line.method_type == "new":
                line.to_analytic_account_id.write(
                    {
                        "initial_available": line.amount_carry_forward,
                    }
                )
            # Add accumulate amount
            # it will sum amount and carry forward to accumulate analytic.
            accumulate_analytic = line.accumulate_analytic_account_id
            amount_accumulate = (
                accumulate_analytic.initial_available + line.amount_accumulate
            )
            accumulate_analytic.write(
                {
                    "initial_available": amount_accumulate,
                }
            )

    def _get_domain_analytic_account_ids(self):
        return []

    def _get_relate_analytic_account_ids(self):
        analytic_account_ids = self.env["account.analytic.account"].search(
            self._get_domain_analytic_account_ids()
        )
        return analytic_account_ids

    def action_budget_carry_forward_info(self):
        self.ensure_one()
        wizard = self.env.ref("budget_control.view_budget_move_forward_info_form")
        forward_id = self._context.get("forward_id", False)
        analytic_account_ids = self._get_relate_analytic_account_ids()
        return {
            "name": _("View Budget Info"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "budget.move.forward.info",
            "views": [(wizard.id, "form")],
            "view_id": wizard.id,
            "target": "new",
            "context": {
                "default_forward_id": forward_id,
                "default_forward_info_line_ids": [
                    (0, 0, {"analytic_account_id": aa.id})
                    for aa in analytic_account_ids
                ],
            },
        }

    def action_budget_carry_forward(self):
        """
        Concept carry forward commitment
            1. Reversed budget move each document line
            2. Commit new budget move for carry forward and Update it to next analytic
            3. Updated new budget move to next analytic
        Example
            Analytic A - Budget Period 2020 - From 01/01/2020 To 31/12/2020
            Analytic A - Budget Period 2021 - From 01/01/2021 To 31/12/2021
        Table of Purchase Budget Move
        =====================================================
        Date       | Analytic Account    | Debit | Credit
        =====================================================
        01/03/2020 | [2020] Analytic A   | 100.0 |
        --------------------Carry Forward--------------------
        01/03/2020 | [2020] Analytic A   |       | 100.0
        01/01/2021 | [2021] Analytic A   | 100.0 |
        """
        self = self.sudo()
        Line = self.env["budget.move.forward.line"]
        for rec in self:
            # Available
            rec.carry_forward_accumulate(rec.forward_accumulate_ids)
            # Commitment
            models = Line._fields["res_model"].selection
            for model in list(dict(models).keys()):
                forward_line = Line.search(
                    [("forward_id", "=", rec.id), ("res_model", "=", model)]
                )
                if not forward_line:
                    continue
                for line in forward_line:
                    line._check_carry_forward_analytic()
                    docline = line.document_id
                    # Find next analytic from method
                    next_analytic = line._get_next_analytic()
                    # clearing commit from next_analytic
                    docline.commit_budget(reverse=True)
                    budget_move = docline.commit_budget()
                    budget_move.write(
                        {
                            "analytic_account_id": next_analytic.id,
                            "date": rec.date_from,
                        }
                    )
                    next_analytic.initial_commit += line.amount_commit
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancel"})


class BudgetMoveForwardLine(models.Model):
    _name = "budget.move.forward.line"
    _description = "Budget Move Forward Line"

    forward_id = fields.Many2one(
        comodel_name="budget.move.forward",
        index=True,
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        index=True,
        required=True,
        readonly=True,
    )
    method_type = fields.Selection(
        METHOD_TYPE,
        string="Method",
        compute="_compute_method_type",
        readonly=False,
        store=True,
        required=True,
    )
    date_extend = fields.Date(
        string="Extended Date",
        related="forward_id.date_extend",
        store=True,
        readonly=False,
    )
    to_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Carry Forward Analytic Account",
        # domain=lambda self: self._get_domain_analytic_account_id(),
        index=True,
    )
    res_model = fields.Selection(
        selection=[],
        string="Res Model",
        required=True,
        readonly=True,
    )
    res_id = fields.Integer(
        string="Res ID",
        required=True,
        readonly=True,
    )
    document_id = fields.Reference(
        selection=[],
        string="Document",
        required=True,
        readonly=True,
    )
    document_number = fields.Char(string="Document Number", readonly=True)
    date_commit = fields.Date(
        string="Date",
        required=True,
        readonly=True,
    )
    amount_commit = fields.Float(
        string="Commitment",
        required=True,
        readonly=True,
    )

    @api.depends("forward_id.method_type")
    def _compute_method_type(self):
        for rec in self:
            rec.method_type = rec.forward_id.method_type

    def _prepare_new_analytic(self):
        for rec in self:
            if rec.method_type == "new":
                analytic_account = rec.analytic_account_id.next_year_analytic()
                rec.write({"to_analytic_account_id": analytic_account})

    def _get_next_analytic(self):
        self.ensure_one()
        next_analytic = False
        if self.method_type == "extend":
            self.analytic_account_id.write(
                {
                    "bm_date_to": self.date_extend,
                }
            )
            # extend not change analytic account
            next_analytic = self.analytic_account_id
        elif self.method_type == "new":
            next_analytic = self.to_analytic_account_id
        return next_analytic

    def _check_carry_forward_analytic(self):
        for rec in self:
            if rec.method_type == "new" and not rec.to_analytic_account_id:
                raise UserError(
                    _(
                        "{} does not have Carry Forward Analytic Account.".format(
                            rec.analytic_account_id.name
                        )
                    )
                )


class BudgetMoveForwardLineAccumulate(models.Model):
    _name = "budget.move.forward.line.accumulate"
    _description = "Budget Move Forward Line Accumulate"

    forward_id = fields.Many2one(
        comodel_name="budget.move.forward",
        index=True,
        readonly=True,
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company", related="forward_id.company_id"
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency", related="forward_id.company_currency_id"
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        required=True,
        readonly=True,
        index=True,
    )
    method_type = fields.Selection(
        METHOD_TYPE,
        string="Method",
        compute="_compute_method_type",
        readonly=False,
        store=True,
        required=True,
    )
    date_extend = fields.Date(
        string="Extended Date",
        related="forward_id.date_extend",
        store=True,
        readonly=False,
    )
    date_from = fields.Date(
        related="forward_id.date_from",
        store=True,
    )
    date_to = fields.Date(
        related="forward_id.date_to",
        store=True,
    )
    to_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Carry Forward Analytic Account",
        index=True,
    )
    amount_carry_forward = fields.Monetary(
        string="Carry Forward Amount",
        currency_field="company_currency_id",
        required=True,
    )
    accumulate_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        compute="_compute_accumulate_analytic_account",
        readonly=False,
        store=True,
    )
    amount_accumulate = fields.Monetary(
        string="Accumulated Amount",
        currency_field="company_currency_id",
        required=True,
    )
    amount_balance = fields.Monetary(
        string="Available",
        currency_field="company_currency_id",
        readonly=True,
    )

    _sql_constraints = [
        (
            "forward_analytic_account_unique",
            "UNIQUE(forward_id, analytic_account_id)",
            "Duplicate analytic account!",
        ),
        (
            "valid_amount_carry_forward",
            "CHECK(amount_carry_forward >= 0)",
            "Carry forward amount must be greater than zero!",
        ),
        (
            "valid_amount_accumulate",
            "CHECK(amount_accumulate >= 0)",
            "Accumulated amount must be greater than zero!",
        ),
    ]

    @api.depends("forward_id.method_type")
    def _compute_method_type(self):
        for rec in self:
            rec.method_type = rec.forward_id.method_type

    @api.depends("forward_id.accumulate_analytic_account_id")
    def _compute_accumulate_analytic_account(self):
        for rec in self:
            rec.accumulate_analytic_account_id = (
                rec.forward_id.accumulate_analytic_account_id
            )

    @api.onchange("method_type")
    def _onchange_reset_method_type(self):
        """ Reset analytic account and extend date all"""
        for line in self:
            line.to_analytic_account_id = False
            line.date_extend = line.forward_id.date_extend

    @api.onchange("amount_carry_forward")
    def _onchange_amount_carry_forward(self):
        for line in self:
            line.amount_accumulate = line.amount_balance - line.amount_carry_forward

    @api.onchange("amount_accumulate")
    def _onchange_amount_accumulate(self):
        for line in self:
            line.amount_carry_forward = line.amount_balance - line.amount_accumulate

    @api.constrains("amount_carry_forward", "amount_accumulate")
    def _check_amount_balance(self):
        for rec in self:
            amount_balance = rec.amount_carry_forward + rec.amount_accumulate
            if (
                float_compare(
                    amount_balance,
                    rec.amount_balance,
                    precision_rounding=self.company_currency_id.rounding,
                )
                > 0
            ):
                raise UserError(
                    _(
                        "{} has sum of carry forward amount and "
                        "accumulted amount more than available amount.".format(
                            rec.analytic_account_id.name
                        )
                    )
                )

    def _prepare_new_analytic(self):
        for rec in self:
            if rec.method_type == "new":
                analytic_account = rec.analytic_account_id.next_year_analytic()
                rec.write({"to_analytic_account_id": analytic_account})

    def _check_constraint_analytic(self):
        for rec in self:
            # There is amount carry forward but no carry forward analytic
            if (
                rec.method_type == "new"
                and rec.amount_carry_forward
                and not rec.to_analytic_account_id
            ):
                raise UserError(
                    _(
                        "{} does not have Carry Forward Analytic Account.".format(
                            rec.analytic_account_id.name
                        )
                    )
                )
            if rec.amount_accumulate and not rec.accumulate_analytic_account_id:
                raise UserError(
                    _(
                        "{} does not have Accumulate Analytic Account.".format(
                            rec.accumulate_analytic_account_id.name
                        )
                    )
                )
