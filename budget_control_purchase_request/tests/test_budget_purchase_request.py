# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.budget_control.tests.common import BudgetControlCommon


@tagged("post_install", "-at_install")
class TestBudgetControlPurchaseRequest(BudgetControlCommon):
    @classmethod
    @freeze_time("2001-02-01")
    def setUpClass(cls):
        super().setUpClass()
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
                ],
            }
        )
        # Test item created for 3 kpi x 4 quarters = 12 budget items
        cls.budget_control.prepare_budget_control_matrix()
        assert len(cls.budget_control.line_ids) == 12
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

    @freeze_time("2001-02-01")
    def _create_purchase_request(self, pr_lines):
        PurchaseRequest = self.env["purchase.request"]
        view_id = "purchase_request.view_purchase_request_form"
        with Form(PurchaseRequest, view=view_id) as pr:
            pr.date_start = datetime.today()
            for pr_line in pr_lines:
                with pr.line_ids.new() as line:
                    line.product_id = pr_line["product_id"]
                    line.product_qty = pr_line["product_qty"]
                    line.estimated_cost = pr_line["estimated_cost"]
                    line.analytic_account_id = pr_line["analytic_id"]
        purchase_request = pr.save()
        return purchase_request

    @freeze_time("2001-02-01")
    def test_01_budget_purchase_request(self):
        """
        On Purchase Request
        (1) Test case, no budget check -> OK
        (2) Check Budget with analytic_kpi -> Error amount exceed on kpi1
        (3) Check Budget with analytic -> OK
        (2) Check Budget with analytic -> Error amount exceed
        """
        # KPI1 = 100, KPI2 = 200, Total = 300
        self.assertEqual(300, self.budget_control.amount_budget)
        # Prepare PR
        purchase_request = self._create_purchase_request(
            [
                {
                    "product_id": self.product1,  # KPI1 = 101 -> error
                    "product_qty": 1,
                    "estimated_cost": 101,
                    "analytic_id": self.costcenter1,
                },
                {
                    "product_id": self.product2,  # KPI2 = 198
                    "product_qty": 2,
                    "estimated_cost": 198,  # This is the price of qty 2
                    "analytic_id": self.costcenter1,
                },
            ]
        )
        # (1) No budget check first
        self.budget_period.control_budget = False
        self.budget_period.control_level = "analytic_kpi"
        # force date commit, as freeze_time not work for write_date
        purchase_request = purchase_request.with_context(
            force_date_commit=purchase_request.date_start
        )
        self.assertEqual(self.budget_control.amount_balance, 300)
        purchase_request.button_to_approve()
        purchase_request.button_approved()  # No budget check no error
        # (2) Check Budget with analytic_kpi -> Error
        purchase_request.button_draft()
        self.assertEqual(self.budget_control.amount_balance, 300)
        self.budget_period.control_budget = True  # Set to check budget
        # kpi 1 (kpi1) & CostCenter1, will result in $ -1.00
        with self.assertRaises(UserError):
            purchase_request.button_to_approve()
        purchase_request.button_draft()
        # (3) Check Budget with analytic -> OK
        self.budget_period.control_level = "analytic"
        purchase_request.button_to_approve()
        purchase_request.button_approved()
        self.assertEqual(self.budget_control.amount_balance, 1)
        purchase_request.button_draft()
        self.assertEqual(self.budget_control.amount_balance, 300)
        # (4) Amount exceed -> Error
        purchase_request.line_ids.write({"estimated_cost": 150.5})  # Total 301
        # CostCenter1, will result in $ -1.00
        with self.assertRaises(UserError):
            purchase_request.button_to_approve()

    @freeze_time("2001-02-01")
    def test_02_budget_pr_to_po(self):
        """PR to PO normally don't care about Quantity, it will uncommit all"""
        # KPI1 = 100, KPI2 = 200, Total = 300
        self.assertEqual(300, self.budget_control.amount_budget)
        # Prepare PR
        purchase_request = self._create_purchase_request(
            [
                {
                    "product_id": self.product1,  # KPI1 = 30
                    "product_qty": 3,
                    "estimated_cost": 30,
                    "analytic_id": self.costcenter1,
                },
            ]
        )
        # Check budget as analytic
        self.budget_period.control_budget = True
        self.budget_period.purchase = True
        self.budget_period.control_level = "analytic"

        purchase_request = purchase_request.with_context(
            force_date_commit=purchase_request.date_start
        )
        self.assertEqual(self.budget_control.amount_balance, 300)
        purchase_request.button_to_approve()
        purchase_request.button_approved()  # No budget check no error
        # PR Commit = 30, PO Commit = 0, Balance = 270
        self.assertEqual(self.budget_control.amount_purchase_request, 30)
        self.assertEqual(self.budget_control.amount_purchase, 0)
        self.assertEqual(self.budget_control.amount_balance, 270)
        # Create PR from PO
        MakePO = self.env["purchase.request.line.make.purchase.order"]
        view_id = "purchase_request.view_purchase_request_line_make_purchase_order"
        ctx = {
            "active_model": "purchase.request",
            "active_ids": [purchase_request.id],
        }
        with Form(MakePO.with_context(**ctx), view=view_id) as w:
            w.supplier_id = self.vendor
        wizard = w.save()
        res = wizard.make_purchase_order()
        purchase = self.env["purchase.order"].search(res["domain"])
        # Change quantity and price_unit of purchase
        self.assertEqual(purchase.order_line[0].product_qty, 3)
        purchase.order_line[0].product_qty = 2
        purchase.order_line[0].price_unit = 25
        purchase = purchase.with_context(force_date_commit=purchase.date_order)
        purchase.button_confirm()
        # PR will return all, PR Commit = 0, PO Commit = 40, Balance = 260
        self.assertEqual(self.budget_control.amount_purchase_request, 0)
        self.assertEqual(self.budget_control.amount_purchase, 50)
        self.assertEqual(self.budget_control.amount_balance, 250)
        # Cancel PO
        purchase.button_cancel()
        self.assertEqual(self.budget_control.amount_purchase_request, 30)
        self.assertEqual(self.budget_control.amount_purchase, 0)
        self.assertEqual(self.budget_control.amount_balance, 270)

    @freeze_time("2001-02-01")
    def test_03_budget_recompute_and_close_budget_move(self):
        """PR to PO (partial PO, but PR will return all)
        - Test recompute on both PR and PO
        - Test close on both PR and PO"""
        # KPI1 = 100, KPI2 = 200, Total = 300
        self.assertEqual(300, self.budget_control.amount_budget)
        # Prepare PR
        purchase_request = self._create_purchase_request(
            [
                {
                    "product_id": self.product1,  # KPI1 = 30
                    "product_qty": 2,
                    "estimated_cost": 30,
                    "analytic_id": self.costcenter1,
                },
                {
                    "product_id": self.product2,  # KPI2 = 40
                    "product_qty": 4,
                    "estimated_cost": 40,
                    "analytic_id": self.costcenter1,
                },
            ]
        )
        # Check budget as analytic
        self.budget_period.control_budget = True
        self.budget_period.purchase = True
        self.budget_period.control_level = "analytic"
        purchase_request = purchase_request.with_context(
            force_date_commit=purchase_request.date_start
        )
        self.assertEqual(self.budget_control.amount_balance, 300)
        purchase_request.button_to_approve()
        purchase_request.button_approved()
        # PR Commit = 30, PO Commit = 0, Balance = 270
        self.assertEqual(self.budget_control.amount_purchase_request, 70)
        self.assertEqual(self.budget_control.amount_purchase, 0)
        # Create PR from PO
        MakePO = self.env["purchase.request.line.make.purchase.order"]
        view_id = "purchase_request.view_purchase_request_line_make_purchase_order"
        ctx = {
            "active_model": "purchase.request",
            "active_ids": [purchase_request.id],
        }
        with Form(MakePO.with_context(**ctx), view=view_id) as w:
            w.supplier_id = self.vendor
        wizard = w.save()
        res = wizard.make_purchase_order()
        purchase = self.env["purchase.order"].search(res["domain"])
        # Change quantity and price_unit of purchase, to commit only
        purchase.order_line[0].write({"product_qty": 1, "price_unit": 15})
        purchase.order_line[1].write({"product_qty": 3, "price_unit": 10})
        purchase = purchase.with_context(force_date_commit=purchase.date_order)
        purchase.button_confirm()
        # PR will return all, PR Commit = 0, PO Commit = 45
        self.assertEqual(self.budget_control.amount_purchase_request, 0)
        self.assertEqual(self.budget_control.amount_purchase, 45)
        # Recompute PR and PO, should be the same.
        purchase_request.recompute_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_purchase_request, 0)
        self.assertEqual(self.budget_control.amount_purchase, 45)
        purchase.recompute_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_purchase_request, 0)
        self.assertEqual(self.budget_control.amount_purchase, 45)
        # Close budget
        purchase_request.close_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_purchase_request, 0)
        self.assertEqual(self.budget_control.amount_purchase, 45)
        purchase.close_budget_move()
        self.budget_control.invalidate_cache()
        self.assertEqual(self.budget_control.amount_purchase_request, 0)
        self.assertEqual(self.budget_control.amount_purchase, 0)
