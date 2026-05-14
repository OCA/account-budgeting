# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountBudgetCommon(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.ref("base.user_root")
        cls.budget_lines_model = cls.env["crossovered.budget.lines"].with_user(cls.user)
        cls.account_model = cls.env["account.account"]

        # Create analytic accounts used across tests (previously referenced
        # via analytic module demo data XMLIDs removed in Odoo 19)
        analytic_plan = cls.env["account.analytic.plan"].search([], limit=1)
        if not analytic_plan:
            analytic_plan = cls.env["account.analytic.plan"].create(
                {"name": "Default Plan (test)"}
            )
        cls.analytic_camp_to_camp = cls.env["account.analytic.account"].create(
            {"name": "Partners Camp to Camp (test)", "plan_id": analytic_plan.id}
        )
        cls.analytic_our_super_product = cls.env["account.analytic.account"].create(
            {"name": "Our Super Product (test)", "plan_id": analytic_plan.id}
        )
        cls.analytic_seagate_p2 = cls.env["account.analytic.account"].create(
            {"name": "Seagate P2 (test)", "plan_id": analytic_plan.id}
        )

        # Create budgets directly (demo data is not loaded in post_install tests)
        year = datetime.datetime.now().year + 1
        cls.budget_pessimistic = cls.env["crossovered.budget"].create(
            {
                "name": f"Budget {year}: Pessimistic",
                "date_from": f"{year}-01-01",
                "date_to": f"{year}-12-31",
            }
        )
        cls.budget_optimistic = cls.env["crossovered.budget"].create(
            {
                "name": f"Budget {year}: Optimistic",
                "date_from": f"{year}-01-01",
                "date_to": f"{year}-12-31",
            }
        )

        # In order to check account budget module in Odoo I created a budget
        # with few budget positions
        # Checking if the budgetary positions have accounts or not
        account_ids = cls.account_model.search(
            [
                ("account_type", "=", "income"),
                ("tag_ids.name", "in", ["Operating Activities"]),
            ]
        ).ids
        if not account_ids:
            account_ids = cls.account_model.create(
                {
                    "name": "Product Sales - (test)",
                    "code": "X2020",
                    "account_type": "income",
                    "tag_ids": [
                        (6, 0, [cls.env.ref("account.account_tag_operating").id])
                    ],
                }
            ).ids
        cls.account_budget_post_sales0 = cls.env["account.budget.post"].create(
            {"name": "Sales", "account_ids": [(6, None, account_ids)]}
        )

        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_camp_to_camp.id,
                "general_budget_id": cls.account_budget_post_sales0.id,
                "date_from": f"{year}-01-01",
                "date_to": f"{year}-01-31",
                "planned_amount": 500.0,
                "crossovered_budget_id": cls.budget_pessimistic.id,
            }
        )
        cls.budget_lines_model.sudo().create(
            {
                "analytic_account_id": cls.analytic_camp_to_camp.id,
                "general_budget_id": cls.account_budget_post_sales0.id,
                "date_from": f"{year}-02-07",
                "date_to": f"{year}-02-28",
                "planned_amount": 900.0,
                "crossovered_budget_id": cls.budget_optimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_camp_to_camp.id,
                "general_budget_id": cls.account_budget_post_sales0.id,
                "date_from": f"{year}-03-01",
                "date_to": f"{year}-03-15",
                "planned_amount": 300.0,
                "crossovered_budget_id": cls.budget_optimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_our_super_product.id,
                "general_budget_id": cls.account_budget_post_sales0.id,
                "date_from": f"{year}-03-16",
                "paid_date": f"{year}-12-03",
                "date_to": f"{year}-03-31",
                "planned_amount": 375.0,
                "crossovered_budget_id": cls.budget_pessimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_our_super_product.id,
                "general_budget_id": cls.account_budget_post_sales0.id,
                "date_from": f"{year}-05-01",
                "paid_date": f"{year}-12-03",
                "date_to": f"{year}-05-31",
                "planned_amount": 375.0,
                "crossovered_budget_id": cls.budget_optimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_seagate_p2.id,
                "general_budget_id": cls.account_budget_post_sales0.id,
                "date_from": f"{year}-07-16",
                "date_to": f"{year}-07-31",
                "planned_amount": 20000.0,
                "crossovered_budget_id": cls.budget_pessimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_seagate_p2.id,
                "general_budget_id": cls.account_budget_post_sales0.id,
                "date_from": f"{year}-02-01",
                "date_to": f"{year}-02-28",
                "planned_amount": 20000.0,
                "crossovered_budget_id": cls.budget_optimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_seagate_p2.id,
                "general_budget_id": cls.account_budget_post_sales0.id,
                "date_from": f"{year}-09-16",
                "date_to": f"{year}-09-30",
                "planned_amount": 10000.0,
                "crossovered_budget_id": cls.budget_pessimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_seagate_p2.id,
                "general_budget_id": cls.account_budget_post_sales0.id,
                "date_from": f"{year}-10-01",
                "date_to": f"{year}-12-31",
                "planned_amount": 10000.0,
                "crossovered_budget_id": cls.budget_optimistic.id,
            }
        )

        account_ids = cls.account_model.search(
            [
                ("account_type", "=", "expense"),
                ("tag_ids.name", "in", ["Operating Activities"]),
            ]
        ).ids

        if not account_ids:
            account_ids = cls.account_model.create(
                {
                    "name": "Expense - (test)",
                    "code": "X2120",
                    "account_type": "expense",
                    "tag_ids": [
                        (6, 0, [cls.env.ref("account.account_tag_operating").id])
                    ],
                }
            ).ids
        cls.account_budget_post_purchase0 = cls.env["account.budget.post"].create(
            {"name": "Purchases", "account_ids": [(6, None, account_ids)]}
        )

        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_camp_to_camp.id,
                "general_budget_id": cls.account_budget_post_purchase0.id,
                "date_from": f"{year}-01-01",
                "date_to": f"{year}-01-31",
                "planned_amount": -500.0,
                "crossovered_budget_id": cls.budget_pessimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_camp_to_camp.id,
                "general_budget_id": cls.account_budget_post_purchase0.id,
                "date_from": f"{year}-02-01",
                "date_to": f"{year}-02-28",
                "planned_amount": -250.0,
                "crossovered_budget_id": cls.budget_optimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_our_super_product.id,
                "general_budget_id": cls.account_budget_post_purchase0.id,
                "date_from": f"{year}-04-01",
                "date_to": f"{year}-04-30",
                "planned_amount": -150.0,
                "crossovered_budget_id": cls.budget_pessimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_seagate_p2.id,
                "general_budget_id": cls.account_budget_post_purchase0.id,
                "date_from": f"{year}-06-01",
                "date_to": f"{year}-06-15",
                "planned_amount": -7500.0,
                "crossovered_budget_id": cls.budget_pessimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_seagate_p2.id,
                "general_budget_id": cls.account_budget_post_purchase0.id,
                "date_from": f"{year}-06-16",
                "date_to": f"{year}-06-30",
                "planned_amount": -5000.0,
                "crossovered_budget_id": cls.budget_pessimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_seagate_p2.id,
                "general_budget_id": cls.account_budget_post_purchase0.id,
                "date_from": f"{year}-07-01",
                "date_to": f"{year}-07-15",
                "planned_amount": -2000.0,
                "crossovered_budget_id": cls.budget_optimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_seagate_p2.id,
                "general_budget_id": cls.account_budget_post_purchase0.id,
                "date_from": f"{year}-08-16",
                "date_to": f"{year}-08-31",
                "planned_amount": -3000.0,
                "crossovered_budget_id": cls.budget_pessimistic.id,
            }
        )
        cls.budget_lines_model.create(
            {
                "analytic_account_id": cls.analytic_seagate_p2.id,
                "general_budget_id": cls.account_budget_post_purchase0.id,
                "date_from": f"{year}-09-01",
                "date_to": f"{year}-09-15",
                "planned_amount": -1000.0,
                "crossovered_budget_id": cls.budget_optimistic.id,
            }
        )
