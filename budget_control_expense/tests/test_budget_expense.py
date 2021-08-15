# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.budget_control.tests.common import BudgetControlCommon


@tagged("post_install", "-at_install")
class TestBudgetControl(BudgetControlCommon):
    @classmethod
    @freeze_time("2001-02-01")
    def setUpClass(cls):
        super().setUpClass()
        # Create sample ready to use Budget Control
        cls.budget_control = cls.BudgetControl.create(
            {
                "name": "CostCenter1/%s" % cls.year,
                "budget_id": cls.budget_period.mis_budget_id.id,
                "analytic_account_id": cls.costcenter1.id,
                "plan_date_range_type_id": cls.date_range_type.id,
                "kpi_ids": [cls.kpi1.id, cls.kpi2.id, cls.kpi3.id],
            }
        )
        # Test item created for 3 kpi x 4 quarters = 12 budget items
        cls.budget_control.prepare_budget_control_matrix()
        assert len(cls.budget_control.item_ids) == 12
        # Assign budget.control amount: KPI1 = 100, KPI2=800, Total=300
        cls.budget_control.item_ids.filtered(
            lambda x: x.kpi_expression_id == cls.kpi1.expression_ids[0]
        )[:1].write({"amount": 100})
        cls.budget_control.item_ids.filtered(
            lambda x: x.kpi_expression_id == cls.kpi2.expression_ids[0]
        )[:1].write({"amount": 200})
        cls.budget_control.allocated_amount = 300
        cls.budget_control.action_done()

    @freeze_time("2001-02-01")
    def _create_expense_sheet(self, ex_lines):
        Expense = self.env["hr.expense"]
        view_id = "hr_expense.hr_expense_view_form"
        ctx = {}
        expense_ids = []
        user = self.env.ref("base.user_admin")
        for ex_line in ex_lines:
            with Form(Expense.with_context(ctx), view=view_id) as ex:
                ex.employee_id = user.employee_id
                ex.product_id = ex_line["product_id"]
                ex.quantity = ex_line["product_qty"]
                ex.unit_amount = ex_line["price_unit"]
                ex.analytic_account_id = ex_line["analytic_id"]
            expense = ex.save()
            expense_ids.append(expense.id)
        expense_sheet = self.env["hr.expense.sheet"].create(
            {
                "name": "Test Expense",
                "employee_id": user.employee_id.id,
                "expense_line_ids": [(6, 0, expense_ids)],
            }
        )
        return expense_sheet

    @freeze_time("2001-02-01")
    def test_01_budget_expense(self):
        """
        On Expense Sheet
        (1) Test case, no budget check -> OK
        (2) Check Budget with analytic_kpi -> Error amount exceed on kpi1
        (3) Check Budget with analytic -> OK
        (2) Check Budget with analytic -> Error amount exceed
        """
        # KPI1 = 100, KPI2 = 200, Total = 300
        self.assertEqual(300, self.budget_control.amount_budget)
        # Prepare Expense Sheet
        expense = self._create_expense_sheet(
            [
                {
                    "product_id": self.product1,  # KPI1 = 101 -> error
                    "product_qty": 1,
                    "price_unit": 101,
                    "analytic_id": self.costcenter1,
                },
                {
                    "product_id": self.product2,  # KPI2 = 198
                    "product_qty": 2,
                    "price_unit": 99,
                    "analytic_id": self.costcenter1,
                },
            ]
        )
        # (1) No budget check first
        self.budget_period.expense = False
        self.budget_period.control_level = "analytic_kpi"
        # force date commit, as freeze_time not work for write_date
        expense = expense.with_context(
            force_date_commit=expense.expense_line_ids[:1].date
        )
        expense.action_submit_sheet()  # No budget check no error
        # (2) Check Budget with analytic_kpi -> Error
        expense.reset_expense_sheets()
        self.budget_period.expense = True  # Set to check budget
        # kpi 1 (kpi1) & CostCenter1, will result in $ -1.00
        with self.assertRaises(UserError):
            expense.action_submit_sheet()
        # (3) Check Budget with analytic -> OK
        expense.reset_expense_sheets()
        self.budget_period.control_level = "analytic"
        expense.action_submit_sheet()
        expense.approve_expense_sheets()
        self.assertEqual(self.budget_control.amount_balance, 1)
        expense.reset_expense_sheets()
        self.assertEqual(self.budget_control.amount_balance, 300)
        # (4) Amount exceed -> Error
        expense.expense_line_ids.write({"unit_amount": 101})
        # CostCenter1, will result in $ -1.00
        with self.assertRaises(UserError):
            expense.action_submit_sheet()

    @freeze_time("2001-02-01")
    def test_02_budget_expense_to_journal_posting(self):
        """ Expense to Journal Posting, commit and uncommit """
        # KPI1 = 100, KPI2 = 200, Total = 300
        self.assertEqual(300, self.budget_control.amount_budget)
        # Prepare Expense on kpi1 with qty 3 and unit_price 10
        expense = self._create_expense_sheet(
            [
                {
                    "product_id": self.product1,  # KPI1 = 101 -> error
                    "product_qty": 3,
                    "price_unit": 10,
                    "analytic_id": self.costcenter1,
                },
            ]
        )
        self.budget_period.expense = True
        self.budget_period.control_level = "analytic"
        expense = expense.with_context(
            force_date_commit=expense.expense_line_ids[:1].date
        )
        expense.action_submit_sheet()
        expense.approve_expense_sheets()
        # Expense = 30, JE Actual = 0, Balance = 270
        self.assertEqual(self.budget_control.amount_expense, 30)
        self.assertEqual(self.budget_control.amount_actual, 0)
        self.assertEqual(self.budget_control.amount_balance, 270)
        # Create and post invoice
        expense.action_sheet_move_create()
        move = expense.account_move_id
        self.assertEqual(move.state, "posted")
        # EX Commit = 0, JE Actual = 30, Balance = 270
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_expense, 0)
        self.assertEqual(self.budget_control.amount_actual, 30)
        self.assertEqual(self.budget_control.amount_balance, 270)
        # # Cancel journal entry
        move.button_cancel()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_expense, 30)
        self.assertEqual(self.budget_control.amount_actual, 0)
        self.assertEqual(self.budget_control.amount_balance, 270)

    @freeze_time("2001-02-01")
    def test_03_budget_recompute_and_close_budget_move(self):
        """EX to JE
        - Test recompute on both EX and JE
        - Test close on both EX and JE"""
        # KPI1 = 100, KPI2 = 200, Total = 300
        self.assertEqual(300, self.budget_control.amount_budget)
        # Prepare Expense on kpi1 with qty 3 and unit_price 10
        expense = self._create_expense_sheet(
            [
                {
                    "product_id": self.product1,
                    "product_qty": 2,
                    "price_unit": 15,
                    "analytic_id": self.costcenter1,
                },
                {
                    "product_id": self.product2,
                    "product_qty": 4,
                    "price_unit": 10,
                    "analytic_id": self.costcenter1,
                },
            ]
        )
        self.budget_period.expense = True
        self.budget_period.control_level = "analytic"
        expense = expense.with_context(
            force_date_commit=expense.expense_line_ids[:1].date
        )
        expense.action_submit_sheet()
        expense.approve_expense_sheets()
        # Expense = 70, JE Actual = 0
        self.assertEqual(self.budget_control.amount_expense, 70)
        self.assertEqual(self.budget_control.amount_actual, 0)
        # Create and post invoice
        expense.action_sheet_move_create()
        move = expense.account_move_id
        self.assertEqual(move.state, "posted")
        # EX Commit = 0, JE Actual = 70
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_expense, 0)
        self.assertEqual(self.budget_control.amount_actual, 70)
        # Recompute
        expense.recompute_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_expense, 0)
        self.assertEqual(self.budget_control.amount_actual, 70)
        move.recompute_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_expense, 0)
        self.assertEqual(self.budget_control.amount_actual, 70)
        # Close
        expense.close_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_expense, 0)
        self.assertEqual(self.budget_control.amount_actual, 70)
        move.close_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_expense, 0)
        self.assertEqual(self.budget_control.amount_actual, 0)
