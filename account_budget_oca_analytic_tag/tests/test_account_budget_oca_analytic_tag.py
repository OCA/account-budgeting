# Copyright (C) 2022 Open Source Integrators (https://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestBudgetAnalyticTag(common.TransactionCase):
    def setUp(self):
        super(TestBudgetAnalyticTag, self).setUp()

        self.budget_position_obj = self.env["account.budget.post"]
        self.exp_account_type = self.env.ref("account.data_account_type_expenses")
        self.company_id = self.env.ref("base.main_company")
        self.analytic_account_id = self.env.ref("analytic.analytic_agrolait")
        self.user_id = self.env.ref("base.user_admin")
        self.partner_id = self.env.ref("base.res_partner_2")
        self.product_id = self.env.ref("product.product_product_8")
        self.budget_position_id = self.test_create_budget_position()

    def test_create_budget_position(self):
        account_ids = (
            self.env["account.account"]
            .search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("user_type_id", "=", self.exp_account_type.id),
                ]
            )
            .ids
        )
        self.account_budget_post_purchase0 = self.env["account.budget.post"].create(
            {"name": "Purchases", "account_ids": [(6, None, account_ids)]}
        )
        return self.budget_position_obj.create(
            {
                "name": "Budget Position",
                "company_id": self.company_id.id,
                "account_ids": [(6, 0, account_ids)],
            }
        )

    def test_budget_creation(self):
        budget_id = self.env["crossovered.budget"].create(
            {
                "name": "Budget 2022",
                "creating_user_id": self.user_id.id,
                "company_id": self.company_id.id,
                "date_from": "2022-01-01",
                "date_to": "2022-06-30",
                "crossovered_budget_line_ids": [
                    (
                        0,
                        0,
                        {
                            "general_budget_id": self.budget_position_id.id,
                            "analytic_account_id": self.analytic_account_id.id,
                            "date_from": "2022-01-01",
                            "date_to": "2022-06-30",
                            "planned_amount": 10000.00,
                        },
                    )
                ],
            }
        )
        # Add line to budget
        line_id = self.env["crossovered.budget.lines"].create(
            {
                "crossovered_budget_id": budget_id.id,
                "date_from": "2022-01-01",
                "date_to": "2022-06-30",
                "general_budget_id": self.budget_position_id.id,
                "planned_amount": 30000.0,
            }
        )
        # Modify budget line
        line_id.write(
            {
                "general_budget_id": self.account_budget_post_purchase0.id,
                "planned_amount": 25000.0,
            }
        )
        budget_id.action_budget_confirm()
        budget_id.action_budget_validate()
