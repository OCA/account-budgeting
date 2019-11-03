# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import datetime
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form


class TestBudgetControl(TransactionCase):
    def setUp(self):
        super(TestBudgetControl, self).setUp()
        self.obj_purchase = self.env['purchase.order']
        self.obj_invoice = self.env['account.invoice']
        self.obj_budget_period = self.env['budget.period']
        self.obj_budget_ctrl = self.env['budget.control']
        self.obj_budget_forward = self.env['budget.move.forward']
        self.obj_budget_transfer = self.env['budget.transfer']
        self.wiz_gen_budget_ctrl = self.env['generate.budget.control']
        self.prev_year = str(datetime.now().year-1)
        self.this_year = str(datetime.now().year)
        self.budget_report = self.env.ref(
            'budget_control_demo_full_cycle.budget_control_1_kpi')
        self.type_quarter = self.env.ref('budget_control_demo_full_cycle.'
                                         'date_range_type_quarter')
        self.group_costcenter = self.env.ref('budget_control_demo_full_cycle.'
                                             'analytic_group_costcenter')
        self.costcenter1 = self.env.ref('budget_control_demo_full_cycle.'
                                        'analytic_costcenter_1')
        self.costcenter2 = self.env.ref('budget_control_demo_full_cycle.'
                                        'analytic_costcenter_2')
        self.costcenter3 = self.env.ref('budget_control_demo_full_cycle.'
                                        'analytic_costcenter_3')

    def create_budget_period(self, year, costcenter_ids=[]):
        all_analytic = not costcenter_ids and True or False
        budget_period = self.obj_budget_period.create(
            {
                'name': 'FY%s' % year,
                'report_id': self.budget_report.id,
                'bm_date_from': '%s-01-01' % year,
                'bm_date_to': '%s-12-31' % year,
                'plan_date_range_type_id': self.type_quarter.id,
                'account': True,
                'purchase_request': True,
                'purchase': True,
                'expense': True,
                'control_all_analytic_accounts': all_analytic,
                'control_analytic_account_ids': [(6, 0, costcenter_ids)]
            }
        )
        return budget_period

    def create_budget_control_by_group(self, budget_period_id,
                                       analytic_group_ids, init_budget=False):
        view_id = "budget_control.view_generate_budget_control"
        ctx = {'active_id': budget_period_id,
               'default_analytic_group_ids': analytic_group_ids,
               'default_all_analytic_accounts': True,
               'default_init_budget_commit': init_budget, }
        f = Form(self.wiz_gen_budget_ctrl.with_context(ctx), view=view_id)
        wizard = f.save()
        wizard.action_generate_budget_control()

    def create_budget_move_forward(self, mis_budget):
        budget_forward = self.obj_budget_forward.create(
            {
                'name': mis_budget.name,
                'to_budget_id': mis_budget.id,
            }
        )
        return budget_forward

    def create_purchase_order(self, analytic, amount, date_order=False):
        product = self.env.ref('product.expense_hotel')
        partner = self.env.ref('base.res_partner_12')  # Azure
        return self.obj_purchase.create({
            'partner_id': partner.id,
            'date_order': date_order or fields.Date.today(),
            'order_line': [(0, 0, {'name': product.name,
                                   'product_id': product.id,
                                   'product_qty': 1.0,
                                   'product_uom': product.uom_id.id,
                                   'price_unit': amount,
                                   'account_analytic_id': analytic.id,
                                   'date_planned': fields.Datetime.now()})]
        })

    def create_invoice(self, analytic, amount, date_invoice=False):
        product = self.env.ref('product.expense_hotel')
        partner = self.env.ref('base.res_partner_12')  # Azure
        view_id = "account.invoice_supplier_form"
        ctx = {'default_type': 'in_invoice',
               'type': 'in_invoice',
               'journal_type': 'purchase',
               }
        with Form(self.obj_invoice.with_context(ctx), view=view_id) as f:
            f.partner_id = partner
            f.date_invoice = date_invoice or fields.Date.today()
            # add support
            with f.invoice_line_ids.new() as line:
                line.product_id = product
                line.quantity = 1.0
                line.price_unit = amount
                line.account_analytic_id = analytic
        invoice = f.save()
        return invoice

    def test_01_no_budget_control_sheet(self):
        """If budget period is set to control any analytic, I excpect that,
        system will check budget even there is no budget control sheet for it.
        """
        self.create_budget_period(self.this_year, [self.costcenter1.id,
                                                       self.costcenter2.id])
        purchase = self.create_purchase_order(self.costcenter1, 100.0)
        with self.assertRaises(UserError) as e:
            purchase.button_confirm()
        self.assertTrue('Budget not sufficient' in e.exception.args[0])

    def test_02_budget_control_amount_exceed(self):
        """If budget control has allocated budget for an analytic,
        but the usage exceed, I expece warning"""
        # For budget to a KPI is set to 4,000, PO > 4000 will raise warning
        # Create budget period, then create budget control sheets
        budget_period = self.create_budget_period(self.this_year,
                                                    [self.costcenter1.id])
        self.create_budget_control_by_group(budget_period.id,
                                            [self.group_costcenter.id],
                                            init_budget=True)
        # Find budget control sheet of this year for costcenter 1
        budget_ctrl = self.obj_budget_ctrl.search([
            ('budget_id', '=', budget_period.mis_budget_id.id),
            ('analytic_account_id', '=', self.costcenter1.id)])
        # According to 1 KPIs x 4 quarter, this result in 4 budget items
        self.assertEqual(len(budget_ctrl.item_ids), 4)
        # Allocate budget 1,000 for each period, total 4,000
        budget_ctrl.item_ids.write({'amount': 1000.0})
        # Test with amount > 4,000, not enough budget
        purchase_over = self.create_purchase_order(self.costcenter1, 4001.0)
        with self.assertRaises(UserError) as e:
            purchase_over.button_confirm()
        self.assertTrue('Budget not sufficient' in e.exception.args[0])
        purchase_over.button_cancel()
        purchase_over.unlink()
        # Test again with amount = 4,000
        purchase = self.create_purchase_order(self.costcenter1, 4000.0)
        purchase.button_confirm()
        # Check budget result on expense KPI, balance is now 0.0
        budgeted = budget_ctrl.get_report_amount(['exp'], ['Budgeted'])
        po_commit = budget_ctrl.get_report_amount(['exp'], ['Purchase'])
        balance = budget_ctrl.get_report_amount(['exp'], ['Available'])
        self.assertEquals((budgeted, po_commit, balance),
                          (4000.0, 4000.0, 0.0))

    def test_03_budget_control_transfer(self):
        """When do budget ransfer, I exept that system will check for,
        - Non negative source amount of eah budget item after transfers
        - Non negative balance of overall budget control
        """
        # Costcenter1 on KPI1/Q1, with budget 1000, transfer to costcenter2
        # - Transfer 1001, show warning
        # - Transfer 1000, successfuly transferred
        # Run report, the commit amount should change.
        def _tranfer(amount):
            return {'source_budget_control_id': budget_ctrl_1.id,
                    'source_item_id': budget_ctrl_1.item_ids[0].id,
                    'target_budget_control_id': budget_ctrl_2.id,
                    'target_item_id': budget_ctrl_2.item_ids[0].id,
                    'amount': amount}

        # To simulate, first create budget of last year.
        budget_period = self.create_budget_period(self.this_year,
                                                    [self.costcenter1.id,
                                                     self.costcenter2.id])
        self.create_budget_control_by_group(budget_period.id,
                                            [self.group_costcenter.id])
        budget_ctrl_1 = self.obj_budget_ctrl.search([
            ('budget_id', '=', budget_period.mis_budget_id.id),
            ('analytic_account_id', '=', self.costcenter1.id)])
        budget_ctrl_2 = self.obj_budget_ctrl.search([
            ('budget_id', '=', budget_period.mis_budget_id.id),
            ('analytic_account_id', '=', self.costcenter2.id)])
        budget_ctrl_1.item_ids.write({'amount': 1000.0})

        # PO commitment 3500
        purchase = self.create_purchase_order(self.costcenter1, 3500.0)
        purchase.button_confirm()
        # Current status of costcente1
        budgeted = budget_ctrl_1.get_report_amount(['total'], ['Budgeted'])
        po_commit = budget_ctrl_1.get_report_amount(['total'], ['Purchase'])
        balance = budget_ctrl_1.get_report_amount(['total'], ['Available'])
        self.assertEquals((budgeted, po_commit, balance),
                          (4000.0, 3500.0, 500.0))

        # 1) Test transfer that result in negative source amount
        budget_transfer = self.obj_budget_transfer.create({
            'name': 'Transfer 1', 'budget_period_id': budget_period.id})
        budget_transfer.write({'transfer_item_ids': [(0, 0, _tranfer(500)),
                                                     (0, 0, _tranfer(501))]})
        with self.assertRaises(ValidationError) as e:
            budget_transfer.action_transfer()
        self.assertTrue('Negative source amount after transfer!',
                        e.exception.name)
        budget_transfer.action_reverse()  # Reverse and so balance remain 500
        balance = budget_ctrl_1.get_report_amount(['total'], ['Available'])
        self.assertEquals(balance, 500.0)

        # 2) Do a successful transfer, and check balance
        budget_transfer = self.obj_budget_transfer.create({
            'name': 'Transfer 1', 'budget_period_id': budget_period.id})
        budget_transfer.write({'transfer_item_ids': [(0, 0, _tranfer(100)),
                                                     (0, 0, _tranfer(200))]})
        budget_transfer.action_transfer()
        balance = budget_ctrl_1.get_report_amount(['total'], ['Available'])
        self.assertEquals(balance, 200.0)

        # 3) Do another transfer, which make balance negative
        budget_transfer = self.obj_budget_transfer.create({
            'name': 'Transfer 1', 'budget_period_id': budget_period.id})
        budget_transfer.write({'transfer_item_ids': [(0, 0, _tranfer(201))]})
        with self.assertRaises(ValidationError) as e:
            budget_transfer.action_transfer()
        balance = budget_ctrl_1.get_report_amount(['total'], ['Available'])
        self.assertEquals(balance, -1)

    def test_04_budget_carry_over(self):
        """ When do budget carry over to new year, I expect that,
        - System will carry over with the amount equal to the commitment
        """
        # On previous year for costcenter1
        #     - Total Budget on 1 KPIs = 4000 (1 KPI = 4 quarter x 1000 = 4000)
        #     - Bill Actual on 1 KPI = 2000
        #     - PO commit = 500
        #     - Budget Balance = 4000-2000-500 = 1500
        # Carry over to new year, only commitment 500 will be carried over,
        #     - PO Commit Carry Forward = 500 on new year
        #     - Budget Carry Over = 500, equal to commitment
        #     - Note that on new year, budget balance will be 0.0
        #
        # To simulate, first create budget of last year.
        prev_budget_period = self.create_budget_period(self.prev_year,
                                                         [self.costcenter1.id])
        self.create_budget_control_by_group(prev_budget_period.id,
                                            [self.group_costcenter.id])
        budget_ctrl = self.obj_budget_ctrl.search([
            ('budget_id', '=', prev_budget_period.mis_budget_id.id),
            ('analytic_account_id', '=', self.costcenter1.id)])
        budget_ctrl.item_ids.write({'amount': 1000.0})
        # Make Actual on previous year -> 3000
        prev_date = '%s-06-06' % self.prev_year
        invoice = self.create_invoice(self.costcenter1, 2000.0, prev_date)
        invoice.action_invoice_open()
        # Commit on previous year on purchases, 200 + 300 = 500
        po1 = self.create_purchase_order(self.costcenter1, 200.0, prev_date)
        po1.with_context({'commit_by_docdate': True}).button_confirm()
        po2 = self.create_purchase_order(self.costcenter1, 300.0, prev_date)
        po2.with_context({'commit_by_docdate': True}).button_confirm()

        # Now, it it is time to close year end and carry forward
        # Create new budget year
        this_budget_period = self.create_budget_period(self.this_year,
                                                         [self.costcenter1.id])
        # Carry commitment forward
        budget_year = this_budget_period.mis_budget_id
        budget_forward = self.create_budget_move_forward(budget_year)
        budget_forward.get_budget_move_forward()
        # Check on forward line, they are still on previous year
        date_commit = budget_forward.forward_line_ids.mapped('date_commit')
        commit = sum(budget_forward.forward_line_ids.mapped('amount_commit'))
        year_forward = str(budget_forward.date_budget_move.year)
        self.assertEqual(str(date_commit[0].year), self.prev_year)
        self.assertEqual(commit, 500.0)
        self.assertEqual(year_forward, self.this_year)
        # Do budget commitment carry forward!
        budget_forward.action_budget_carry_forward()
        budget_forward.get_budget_move_forward()
        # Check again, now the date commit of budget moves are in new year
        date_commit = budget_forward.forward_line_ids.mapped('date_commit')
        self.assertEqual(str(date_commit[0].year), self.this_year)
        # Back to budget period, and generate budget control for this year
        # with init_budget_commit = True, commited amount will be budget intial
        self.create_budget_control_by_group(this_budget_period.id,
                                            [self.group_costcenter.id],
                                            init_budget=True)
        budget_ctrl = self.obj_budget_ctrl.search([
            ('budget_id', '=', this_budget_period.mis_budget_id.id),
            ('analytic_account_id', '=', self.costcenter1.id)])
        # New inital commit is 500, equal to the carry forward amount
        self.assertEquals(sum(budget_ctrl.item_ids.mapped('amount')), 500.0)
        budgeted = budget_ctrl.get_report_amount(['total'], ['Budgeted'])
        po_commit = budget_ctrl.get_report_amount(['total'], ['Purchase'])
        balance = budget_ctrl.get_report_amount(['total'], ['Available'])
        self.assertEquals((budgeted, po_commit, balance),
                          (500.0, 500.0, 0.0))
