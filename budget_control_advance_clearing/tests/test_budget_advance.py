# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.budget_control.tests.common import BudgetControlCommon


@tagged("post_install", "-at_install")
class TestBudgetControlAdvance(BudgetControlCommon):
    @classmethod
    @freeze_time("2001-02-01")
    def setUpClass(cls):
        super().setUpClass()
        # Additional KPI for advance
        cls.kpiAV = cls.BudgetKPI.create({"name": "kpi AV"})
        cls.template_lineAV = cls.env["budget.template.line"].create(
            {
                "template_id": cls.template.id,
                "kpi_id": cls.kpiAV.id,
                "account_ids": [(4, cls.account_kpiAV.id)],
            }
        )

        # Create sample ready to use Budget Control
        cls.budget_control = cls.BudgetControl.create(
            {
                "name": "CostCenter1/%s" % cls.year,
                "template_id": cls.budget_period.template_id.id,
                "budget_period_id": cls.budget_period.id,
                "analytic_account_id": cls.costcenter1.id,
                "plan_date_range_type_id": cls.date_range_type.id,
                "template_line_ids": [
                    cls.template_line1.id,
                    cls.template_line2.id,
                    cls.template_line3.id,
                    cls.template_lineAV.id,
                ],
            }
        )
        # Test item created for 4 kpi x 4 quarters = 16 budget items
        cls.budget_control.prepare_budget_control_matrix()
        assert len(cls.budget_control.line_ids) == 16
        # Assign budget.control amount: KPI1 = 100, KPI2=800, Total=300
        cls.budget_control.line_ids.filtered(lambda x: x.kpi_id == cls.kpi1)[:1].write(
            {"amount": 100}
        )
        cls.budget_control.line_ids.filtered(lambda x: x.kpi_id == cls.kpi2)[:1].write(
            {"amount": 200}
        )
        cls.budget_control.flush()  # Need to flush data into table, so it can be sql
        cls.budget_control.allocated_amount = 300
        cls.budget_control.action_done()
        # Set advance account
        product = cls.env.ref("hr_expense_advance_clearing.product_emp_advance")
        product.property_account_expense_id = cls.account_kpiAV

    @freeze_time("2001-02-01")
    def _create_advance_sheet(self, amount, analytic):
        Expense = self.env["hr.expense"]
        view_id = "hr_expense_advance_clearing.hr_expense_view_form"
        user = self.env.ref("base.user_admin")
        with Form(Expense.with_context(default_advance=True), view=view_id) as ex:
            ex.employee_id = user.employee_id
            ex.unit_amount = amount
            ex.analytic_account_id = analytic
        advance = ex.save()
        expense_sheet = self.env["hr.expense.sheet"].create(
            {
                "name": "Test Advance",
                "employee_id": user.employee_id.id,
                "expense_line_ids": [(6, 0, [advance.id])],
            }
        )
        return expense_sheet

    @freeze_time("2001-02-01")
    def _create_clearing_sheet(self, advance, ex_lines):
        Expense = self.env["hr.expense"]
        view_id = "hr_expense_advance_clearing.hr_expense_view_form"
        expense_ids = []
        user = self.env.ref("base.user_admin")
        for ex_line in ex_lines:
            with Form(Expense, view=view_id) as ex:
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
                "advance_sheet_id": advance and advance.id,
                "employee_id": user.employee_id.id,
                "expense_line_ids": [(6, 0, expense_ids)],
            }
        )
        return expense_sheet

    @freeze_time("2001-02-01")
    def test_01_budget_advance(self):
        """
        Create Advance,
        - Budget will be committed into advance.budget.move
        - No actual on JE
        """
        # KPI1 = 100, KPI2 = 200, Total = 300
        self.assertEqual(300, self.budget_control.amount_budget)
        # Create advance = 100
        advance = self._create_advance_sheet(100, self.costcenter1)
        # (1) No budget check first
        self.budget_period.advance = False
        self.budget_period.control_level = "analytic_kpi"
        # force date commit, as freeze_time not work for write_date
        advance = advance.with_context(
            force_date_commit=advance.expense_line_ids[:1].date
        )
        advance.action_submit_sheet()  # No budget check no error
        # (2) Check Budget with analytic_kpi -> Error
        advance.reset_expense_sheets()
        self.budget_period.control_budget = True  # Set to check budget
        # kpi 1 (kpi1) & CostCenter1, will result in $ -1.00
        with self.assertRaises(UserError):
            advance.action_submit_sheet()
        # (3) Check Budget with analytic -> OK
        self.budget_period.control_level = "analytic"
        advance.action_submit_sheet()
        advance.approve_expense_sheets()
        self.assertEqual(self.budget_control.amount_advance, 100)
        self.assertEqual(self.budget_control.amount_balance, 200)
        # Post journal entry
        advance.action_sheet_move_create()
        move = advance.account_move_id
        self.assertEqual(move.state, "posted")
        self.assertTrue(move.not_affect_budget)
        self.assertFalse(move.budget_move_ids)
        self.assertEqual(self.budget_control.amount_advance, 100)
        self.assertEqual(self.budget_control.amount_actual, 0)
        self.assertEqual(self.budget_control.amount_balance, 200)
        # Reset
        advance.reset_expense_sheets()
        self.assertEqual(self.budget_control.amount_advance, 0)
        self.assertEqual(self.budget_control.amount_balance, 300)
        # (4) Amount exceed -> Error
        advance.expense_line_ids.write({"unit_amount": 301})
        # CostCenter1, will result in $ -1.00
        with self.assertRaises(UserError):
            advance.action_submit_sheet()

    @freeze_time("2001-02-01")
    def test_02_budget_advance_clearing(self):
        """Advance 100 (which is equal to budget amount), with clearing cases when,
        - Clearing 80, the uncommit advance should be 20
        - Clearing 120, the uncommit advance should be 100 (max)
        """
        # KPI1 = 100, KPI2 = 200, Total = 300
        self.assertEqual(300, self.budget_control.amount_budget)
        # Create advance = 100
        advance = self._create_advance_sheet(100, self.costcenter1)
        self.budget_period.control_budget = True
        self.budget_period.control_level = "analytic"
        advance = advance.with_context(
            force_date_commit=advance.expense_line_ids[:1].date
        )
        advance.action_submit_sheet()
        advance.approve_expense_sheets()
        advance.action_sheet_move_create()
        # Advance 100, Clearing = 0, Balance = 200
        self.assertEqual(self.budget_control.amount_advance, 100)
        self.assertEqual(self.budget_control.amount_expense, 0)
        self.assertEqual(self.budget_control.amount_balance, 200)
        # Create Clearing = 80 to this advance
        clearing = self._create_clearing_sheet(
            advance,
            [
                {
                    "product_id": self.product1,  # KPI1 = 20
                    "product_qty": 1,
                    "price_unit": 20,
                    "analytic_id": self.costcenter1,
                },
                {
                    "product_id": self.product2,  # KPI2 = 80
                    "product_qty": 2,
                    "price_unit": 30,
                    "analytic_id": self.costcenter1,
                },
            ],
        )
        clearing = clearing.with_context(
            force_date_commit=clearing.expense_line_ids[:1].date
        )
        clearing.action_submit_sheet()
        clearing.approve_expense_sheets()
        # Advance 20, Clearing = 80, Balance = 200
        self.assertEqual(self.budget_control.amount_advance, 20)
        self.assertEqual(self.budget_control.amount_expense, 80)
        self.assertEqual(self.budget_control.amount_balance, 200)
        # Refuse
        clearing.refuse_sheet("Refuse it!")
        self.assertEqual(self.budget_control.amount_advance, 100)
        self.assertEqual(self.budget_control.amount_expense, 0)
        self.assertEqual(self.budget_control.amount_balance, 200)
        # Change line 1 amount to exceed
        clearing.expense_line_ids[:1].unit_amount = 200
        self.budget_control.flush()
        with self.assertRaises(UserError):
            clearing.action_submit_sheet()

    @freeze_time("2001-02-01")
    def test_03_budget_recompute_and_close_budget_move(self):
        """
        After Advance 20, Clearing 80
        - Recompute both should be the same
        - Close budget both should be all zero
        """
        # KPI1 = 100, KPI2 = 200, Total = 300
        self.assertEqual(300, self.budget_control.amount_budget)
        # Create advance = 100
        advance = self._create_advance_sheet(100, self.costcenter1)
        self.budget_period.control_budget = True
        self.budget_period.control_level = "analytic"
        advance = advance.with_context(
            force_date_commit=advance.expense_line_ids[:1].date
        )
        advance.action_submit_sheet()
        advance.approve_expense_sheets()
        advance.action_sheet_move_create()
        # Create Clearing = 80 to this advance
        clearing = self._create_clearing_sheet(
            advance,
            [
                {
                    "product_id": self.product1,  # KPI1 = 20
                    "product_qty": 1,
                    "price_unit": 20,
                    "analytic_id": self.costcenter1,
                },
                {
                    "product_id": self.product2,  # KPI2 = 80
                    "product_qty": 2,
                    "price_unit": 30,
                    "analytic_id": self.costcenter1,
                },
            ],
        )
        clearing = clearing.with_context(
            force_date_commit=clearing.expense_line_ids[:1].date
        )
        clearing.action_submit_sheet()
        clearing.approve_expense_sheets()
        # Advance 20, Clearing = 80, Balance = 200
        self.assertEqual(self.budget_control.amount_advance, 20)
        self.assertEqual(self.budget_control.amount_expense, 80)
        # Recompute
        advance.recompute_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_advance, 20)
        self.assertEqual(self.budget_control.amount_expense, 80)
        clearing.recompute_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_advance, 20)
        self.assertEqual(self.budget_control.amount_expense, 80)
        # Close
        advance.close_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_advance, 0)
        self.assertEqual(self.budget_control.amount_expense, 80)
        clearing.close_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_advance, 0)
        self.assertEqual(self.budget_control.amount_expense, 0)

    @freeze_time("2001-02-01")
    def test_04_return_advance(self):
        """
        Create Advance 100, balance is 200
        - Return Advance 30
        - Balance should be 230
        """
        # KPI1 = 100, KPI2 = 200, Total = 300
        self.assertEqual(300, self.budget_control.amount_budget)
        # Create advance = 100
        advance = self._create_advance_sheet(100, self.costcenter1)
        self.budget_period.control_budget = True
        self.budget_period.control_level = "analytic"
        advance = advance.with_context(
            force_date_commit=advance.expense_line_ids[:1].date
        )
        advance.action_submit_sheet()
        advance.approve_expense_sheets()
        advance.action_sheet_move_create()
        # Make payment full amount = 100
        advance.action_register_payment()
        f = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=[advance.account_move_id.id],
            )
        )
        wizard = f.save()
        wizard.action_create_payments()
        self.assertEqual(advance.clearing_residual, 100)
        self.assertEqual(self.budget_control.amount_advance, 100)
        self.assertEqual(self.budget_control.amount_balance, 200)
        # Return advance = 30
        advance.with_context(
            hr_return_advance=True,
        ).action_register_payment()
        with Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=[advance.account_move_id.id],
                hr_return_advance=True,
            )
        ) as f:
            f.payment_date = fields.Date.today()
            f.amount = 30
        wizard = f.save()
        wizard.with_context(
            hr_return_advance=True,
        ).action_create_payments()
        self.assertEqual(advance.clearing_residual, 70)
        self.assertEqual(self.budget_control.amount_advance, 70)
        self.assertEqual(self.budget_control.amount_balance, 230)
