# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.budget_control.tests.common import BudgetControlCommon


@tagged("post_install", "-at_install")
class TestBudgetPlan(BudgetControlCommon):
    @classmethod
    @freeze_time("2001-02-01")
    def setUpClass(cls):
        super().setUpClass()
        cls.BudgetPlan = cls.env["budget.plan"]
        # Create sample ready to use Budget Control
        cls.budget_control = cls.BudgetControl.create(
            {
                "name": "CostCenter1/2002",
                "template_id": cls.budget_period.template_id.id,
                "budget_period_id": cls.budget_period.id,
                "analytic_account_id": cls.costcenter1.id,
                "plan_date_range_type_id": cls.date_range_type.id,
                "template_line_ids": [
                    cls.template_line1.id,
                    cls.template_line2.id,
                    cls.template_line3.id,
                ],
            }
        )
        # Test item created for 3 kpi x 4 quarters = 12 budget items
        cls.budget_control.prepare_budget_control_matrix()
        assert len(cls.budget_control.line_ids) == 12
        # Assign budget.control amount: KPI1 = 100, KPI2=200, Total=300
        cls.budget_control.line_ids.filtered(lambda x: x.kpi_id == cls.kpi1)[:1].write(
            {"amount": 100}
        )
        cls.budget_control.line_ids.filtered(lambda x: x.kpi_id == cls.kpi2)[:1].write(
            {"amount": 200}
        )
        cls.budget_control.flush()  # Need to flush data into table, so it can be sql
        cls.budget_control.allocated_amount = 300
        cls.budget_control.action_done()

    @freeze_time("2001-02-01")
    def test_01_create_budget_plan(self):
        """
        Test normal process create budget plan
        """
        budget_plan = self.BudgetPlan.create(
            {
                "name": "Budget Plan Test {}".format(self.year),
                "budget_period_id": self.budget_period.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "analytic_account_id": self.costcenter1.id,
                            "amount": 100.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "analytic_account_id": self.costcenterX.id,
                            "amount": 200.0,
                        },
                    ),
                ],
            }
        )
        self.assertEqual(len(budget_plan.line_ids), 2)
        self.assertEqual(budget_plan.state, "draft")
        self.assertEqual(budget_plan.total_amount, 300.0)
        self.assertFalse(budget_plan.line_ids[0].allocated_amount)
        self.assertFalse(budget_plan.line_ids[0].released_amount)
        self.assertEqual(budget_plan.line_ids[0].amount, 100.0)
        budget_plan.action_confirm()
        self.assertEqual(budget_plan.state, "confirm")
        # After confirm, it will update allocated, released following amount
        self.assertEqual(budget_plan.line_ids[0].allocated_amount, 100.0)
        self.assertEqual(budget_plan.line_ids[0].released_amount, 100.0)
        self.assertEqual(budget_plan.line_ids[0].amount, 100.0)
        # Analytic has 1 budget control from create manual
        self.assertEqual(len(budget_plan.line_ids[0].budget_control_ids), 1)
        self.assertFalse(len(budget_plan.line_ids[1].budget_control_ids))
        # Archive budget control created before plan
        self.budget_control.active = False
        self.assertFalse(budget_plan.line_ids[0].budget_control_ids)
        # Create budget controls
        budget_plan.action_create_update_budget_control()
        self.assertEqual(len(budget_plan.line_ids[0].budget_control_ids), 1)
        self.assertEqual(len(budget_plan.line_ids[1].budget_control_ids), 1)
        # Budget count is not include active
        self.assertEqual(budget_plan.budget_control_count, 2)
        action = budget_plan.button_open_budget_control()
        self.assertEqual(action["domain"][0][2], budget_plan.budget_control_ids.ids)
        budget_plan.action_done()
        # Test update consumed amount
        self.assertEqual(budget_plan.line_ids[0].amount_consumed, 0.0)
        invoice = self._create_invoice(
            "in_invoice",
            self.vendor,
            datetime.today(),
            self.costcenter1,
            [{"account": self.account_kpi1, "price_unit": 100}],
        )
        invoice.action_post()
        budget_plan.action_update_plan()
        self.assertEqual(budget_plan.line_ids[0].amount_consumed, 100.0)
        self.assertEqual(budget_plan.state, "done")
        budget_plan.action_cancel()
        self.assertEqual(budget_plan.state, "cancel")
        budget_plan.action_draft()
        self.assertEqual(budget_plan.state, "draft")
        # Check new amount can not less than consumed amount
        budget_plan.line_ids[0].amount = 70
        with self.assertRaises(UserError):
            budget_plan.action_confirm()
