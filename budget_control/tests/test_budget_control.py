# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from dateutil.rrule import MONTHLY

from odoo.exceptions import UserError
from odoo.tests.common import SavepointCase


class TestMisBudget(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.year = datetime.datetime.now().year
        RangeType = cls.env["date.range.type"]
        Analytic = cls.env["account.analytic.account"]
        BudgetControl = cls.env["budget.control"]
        # Create quarterly date range for current year
        cls.date_range_type = RangeType.create({"name": "TestQuarter"})
        cls._create_date_range_quarter(cls)
        # Create budget kpi
        cls.report = cls._create_mis_report_kpi(cls)
        # Create budget.period for current year
        cls.budget_period = cls._create_budget_period_fy(
            cls, cls.report.id, cls.date_range_type.id
        )
        # Create budget.control for CostCenter1,
        #  by selected budget_id and date range (by quarter)
        cls.costcenter1 = Analytic.create({"name": "CostCenter1"})
        cls.budget_control = BudgetControl.create(
            {
                "name": "CostCenter1/%s",
                "budget_id": cls.budget_period.mis_budget_id.id,
                "analytic_account_id": cls.costcenter1.id,
                "plan_date_range_type_id": cls.date_range_type.id,
            }
        )
        # Test item created for 3 kpi x 4 quarters = 12 budget items
        assert len(cls.budget_control.item_ids) == 12
        # Assign budget.control amount: KPI1 = 100x4=400, KPI2=800, KPI3=1,200
        cls.budget_control.item_ids.filtered(
            lambda l: l.kpi_expression_id == cls.kpi1.expression_ids[0]
        ).write({"amount": 100})
        cls.budget_control.item_ids.filtered(
            lambda l: l.kpi_expression_id == cls.kpi2.expression_ids[0]
        ).write({"amount": 200})
        cls.budget_control.item_ids.filtered(
            lambda l: l.kpi_expression_id == cls.kpi3.expression_ids[0]
        ).write({"amount": 300})
        # Assign product to purchase using KPI1, KPI2, KPI3 account codes
        cls.product_kpi1 = cls.env.ref("product.product_product_6")
        cls.product_kpi1.property_account_expense_id = cls.account_kpi1
        cls.product_kpi2 = cls.env.ref("product.product_product_7")
        cls.product_kpi2.property_account_expense_id = cls.account_kpi2
        cls.product_kpi3 = cls.env.ref("product.product_product_8")
        cls.product_kpi3.property_account_expense_id = cls.account_kpi3
        # Vendor
        cls.vendor = cls.env.ref("base.res_partner_12")

    def _create_date_range_quarter(self):
        Generator = self.env["date.range.generator"]
        generator = Generator.create(
            {
                "date_start": "%s-01-01" % self.year,
                "name_prefix": "%s/Test/Q-" % self.year,
                "type_id": self.date_range_type.id,
                "duration_count": 3,
                "unit_of_time": str(MONTHLY),
                "count": 4,
            }
        )
        generator.action_apply()

    def _create_mis_report_kpi(self):
        Account = self.env["account.account"]
        type_exp = self.env.ref("account.data_account_type_expenses").id
        self.account_kpi1 = Account.create(
            {"name": "KPI1", "code": "KPI1", "user_type_id": type_exp}
        )
        self.account_kpi2 = Account.create(
            {"name": "KPI2", "code": "KPI2", "user_type_id": type_exp}
        )
        self.account_kpi3 = Account.create(
            {"name": "KPI3", "code": "KPI3", "user_type_id": type_exp}
        )
        # create report
        report = self.env["mis.report"].create(
            dict(
                name="Test KPI",
            )
        )
        self.kpi1 = self.env["mis.report.kpi"].create(
            dict(
                report_id=report.id,
                name="kpi1",
                budgetable=True,
                description="kpi 1",
                expression="balp[KPI1]",
            )
        )
        self.kpi2 = self.env["mis.report.kpi"].create(
            dict(
                report_id=report.id,
                name="kpi2",
                budgetable=True,
                description="kpi 2",
                expression="balp[KPI2]",
            )
        )
        self.kpi3 = self.env["mis.report.kpi"].create(
            dict(
                report_id=report.id,
                name="kpi3",
                budgetable=True,
                description="kpi 3",
                expression="balp[KPI3]",
            )
        )
        return report

    def _create_budget_period_fy(self, report_id, date_range_type_id):
        BudgetPeriod = self.env["budget.period"]
        budget_period = BudgetPeriod.create(
            {
                "name": "Budget for FY%s" % self.year,
                "report_id": report_id,
                "bm_date_from": "%s-01-01" % self.year,
                "bm_date_to": "%s-12-31" % self.year,
                "plan_date_range_type_id": date_range_type_id,
                "control_level": "analytic_kpi",
            }
        )
        return budget_period

    def _create_invoice(self, inv_type, vendor, analytic, invoice_lines):
        Invoice = self.env["account.move"]
        invoice = Invoice.create(
            {
                "partner_id": vendor,
                "move_type": inv_type,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": line.get("product"),
                            "price_unit": line.get("price_unit"),
                            "quantity": 1,
                            "analytic_account_id": analytic,
                        },
                    )
                    for line in invoice_lines
                ],
            }
        )
        return invoice

    def test_01_vendor_blll_budget_check(self):
        """If budget.period is set to check budget, KPI1=400.0 allocated
        - First 400.0 will used all budget allocated
        - Second 1.0 will make it exceed"""
        # Control Budget by Analytic & KPI
        # Check budget
        self.budget_period.account = True
        bill1 = self._create_invoice(
            "in_invoice",
            self.vendor,
            self.costcenter1,
            [{"product": self.product_kpi1, "price_unit": 400.0}],
        )  # Equal budget
        bill1.action_post()
        # 1.0 amount will exceed the budget, and throw error
        bill2 = self._create_invoice(
            "in_invoice",
            self.vendor,
            self.costcenter1,
            [{"product": self.product_kpi1, "price_unit": 1.0}],
        )
        with self.assertRaises(UserError):
            bill2.action_post()

        # Control Budget by Analytic, It should used budget allocated
        self.budget_period.control_level = "analytic"
        bill2.action_post()

    def test_02_vendor_blll_no_budget_check(self):
        """If budget.period is not set to check budget, no budget check"""
        # No budget check
        self.budget_period.account = False
        bill1 = self._create_invoice(
            "in_invoice",
            self.vendor,
            self.costcenter1,
            [{"product": self.product_kpi1, "price_unit": 100000.0}],
        )  # big amount
        bill1.action_post()

    def test_03_refund_budget_check(self):
        """For refund, always not checking"""
        # First, make budget actual to exceed budget first
        self.budget_period.account = False  # No budget check first
        bill1 = self._create_invoice(
            "in_invoice",
            self.vendor,
            self.costcenter1,
            [{"product": self.product_kpi1, "price_unit": 100000.0}],
        )  # big amount
        bill1.action_post()
        # Check budget, for in_refund, force no budget check
        self.budget_period.account = True
        invoice = self._create_invoice(
            "in_refund",
            self.vendor,
            self.costcenter1,
            [{"product": self.product_kpi1, "price_unit": 100.0}],
        )
        invoice.action_post()
