# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class BaseBudgetMove(models.AbstractModel):
    _name = "base.budget.move"
    _description = "Abstract class to be extended by budgt commit documents"

    date = fields.Date(
        required=True,
        index=True,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account",
        auto_join=True,
        index=True,
        readonly=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        auto_join=True,
        index=True,
        readonly=True,
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag",
        string="Analytic Tags",
    )
    amount_currency = fields.Float(
        required=True,
        help="Amount in multi currency",
    )
    credit = fields.Float(
        readonly=True,
    )
    debit = fields.Float(
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id.id,
        index=True,
    )


class BudgetDoclineMixin(models.AbstractModel):
    _name = "budget.docline.mixin"
    _description = "Mixin used in each document line model that commit budget"

    amount_commit = fields.Float(
        compute="_compute_commit",
        store=True,
    )
    date_commit = fields.Date(
        compute="_compute_commit",
        store=True,
    )

    @api.depends("budget_move_ids", "budget_move_ids.date")
    def _compute_commit(self):
        for rec in self:
            if not rec.budget_move_ids:
                continue
            debit = sum(rec.budget_move_ids.mapped("debit"))
            credit = sum(rec.budget_move_ids.mapped("credit"))
            rec.amount_commit = debit - credit
            rec.date_commit = min(rec.budget_move_ids.mapped("date"))

    def _prepare_budget_commitment(
        self,
        account,
        analytic_account,
        doc_date,
        amount_currency,
        currency,
        reverse=False,
    ):
        self.ensure_one()
        company = self.env.user.company_id
        amount = (
            currency
            and currency._convert(
                amount_currency, company.currency_id, company, doc_date
            )
            or amount_currency
        )
        res = {
            "account_id": account.id,
            "analytic_account_id": analytic_account.id,
            "date": (
                self._context.get("commit_by_docdate")
                and doc_date
                or fields.Date.today()
            ),
            "amount_currency": amount_currency,
            "debit": not reverse and amount or 0.0,
            "credit": reverse and amount or 0.0,
            "company_id": company.id,
        }
        return res
