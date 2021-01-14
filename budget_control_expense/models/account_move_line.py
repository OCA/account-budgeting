# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_date_budget_commitment(self):
        model = self._context.get("active_model", False)
        move_type = self._context.get("default_move_type", False)
        if model == "hr.expense" and not move_type:
            expense = self.env[model].browse(self._context.get("active_id", []))
            return expense.date
        return super()._get_date_budget_commitment()

    def _check_amount_currency_tax(self, date, doc_type="account"):
        self.ensure_one()
        amount_currency = super()._check_amount_currency_tax(date, doc_type)
        if self.expense_id:
            budget_period = self.env["budget.period"]._get_eligible_budget_period(
                date, doc_type
            )
            price = self._get_price_total_and_subtotal_model(
                self.amount_currency,
                self.quantity,
                self.discount,
                self.currency_id,
                self.product_id,
                self.partner_id,
                self.tax_ids,
                "entry",
            )
            amount_currency = (
                budget_period.include_tax
                and price.get("price_total", 0.0)
                or self.amount_currency
            )
        return amount_currency
