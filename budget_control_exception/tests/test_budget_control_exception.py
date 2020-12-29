# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.budget_control.tests.test_budget_control import TestMisBudget


class TestBudgetControlRevision(TestMisBudget):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.BudgetControl = cls.env["budget.control"]
        cls.BudgetControlExceptionConfirm = cls.env["budget.control.exception.confirm"]

        cls.partner_id = cls.env.ref("base.res_partner_1")
        cls.exception_checkassignee = cls.env.ref(
            "budget_control_exception.bc_excep_assignee_check"
        )
        cls.exception_checkamount = cls.env.ref(
            "budget_control_exception.bc_excep_amount_plan_check"
        )

    def _check_normal_process(self):
        self.assertEqual(self.budget_control.state, "draft")
        self.budget_control.action_done()
        self.assertEqual(self.budget_control.state, "done")
        # reset
        self.budget_control.action_draft()

    def test_01_budget_control_exception(self):
        self.exception_checkassignee.active = True
        # Normally Case
        self.budget_control.assignee_id = self.partner_id.id
        self._check_normal_process()
        # Exception Case
        self.budget_control.assignee_id = False
        self.assertEqual(self.budget_control.state, "draft")
        self.budget_control.action_done()
        self.assertEqual(self.budget_control.state, "draft")

        self.budget_control.test_all_draft_orders()
        self.assertEqual(self.budget_control.state, "draft")

        self.budget_control.ignore_exception = True
        self.budget_control.action_done()
        self.assertEqual(self.budget_control.state, "done")

    def test_02_budget_plan_exception(self):
        self.exception_checkamount.active = True
        # Normally Case
        self.assertTrue(all(plan.amount > 0 for plan in self.budget_control.item_ids))
        self._check_normal_process()
        # Exception Case
        self.budget_control.item_ids[0].amount = -1
        self.assertEqual(self.budget_control.state, "draft")
        self.budget_control.action_done()
        self.assertEqual(self.budget_control.state, "draft")

        self.budget_control.test_all_draft_orders()
        self.assertEqual(self.budget_control.state, "draft")

        self.budget_control.ignore_exception = True
        self.budget_control.action_done()
        self.assertEqual(self.budget_control.state, "done")
