# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
from dateutil.rrule import MONTHLY
from odoo.tests.common import TransactionCase
from odoo.tests.common import Form
from odoo.exceptions import UserError


class TestMisBudget(TransactionCase):

    def setUp(self):
        super(TestMisBudget, self).setUp()
        self.year = datetime.datetime.now().year
        RangeType = self.env['date.range.type']
        Analytic = self.env['account.analytic.account']
        BudgetControl = self.env['budget.control']
        # Create quarterly date range for current year
        self.date_range_type = RangeType.create({'name': 'TestQuarter'})
        self._create_date_range_quarter()
        # Create budget kpi
        self.report = self._create_mis_report_kpi()
        # Create budget.period for current year
        self.budget_period = self._create_budget_period_fy(self.report.id)
        # Create budget.control for CostCenter1,
        #  by selected budget_id and date range (by quarter)
        self.costcenter1 = Analytic.create({'name': 'CostCenter1'})
        self.budget_control = BudgetControl.create({
            'name': 'CostCenter1/%s',
            'budget_id': self.budget_period.mis_budget_id.id,
            'analytic_account_id': self.costcenter1.id,
            'plan_date_range_type_id': self.date_range_type.id})
        # Test item created for 3 kpi x 4 quarters = 12 budget items
        self.assertEquals(len(self.budget_control.item_ids), 12)
        # Assign budget.control amount: KPI1 = 100x4=400, KPI2=800, KPI3=1,200
        self.budget_control.item_ids.filtered(
            lambda l: l.kpi_expression_id == self.kpi1.expression_ids[0]).\
            write({'amount': 100})
        self.budget_control.item_ids.filtered(
            lambda l: l.kpi_expression_id == self.kpi2.expression_ids[0]).\
            write({'amount': 200})
        self.budget_control.item_ids.filtered(
            lambda l: l.kpi_expression_id == self.kpi3.expression_ids[0]).\
            write({'amount': 300})
        # Assign product to purchase using KPI1, KPI2, KPI3 account codes
        self.product_kpi1 = self.env.ref('product.product_product_6')
        self.product_kpi1.property_account_expense_id = self.account_kpi1
        self.product_kpi2 = self.env.ref('product.product_product_7')
        self.product_kpi2.property_account_expense_id = self.account_kpi2
        self.product_kpi3 = self.env.ref('product.product_product_8')
        self.product_kpi3.property_account_expense_id = self.account_kpi3
        # Vendor
        self.vendor = self.env.ref('base.res_partner_12')

    def _create_date_range_quarter(self):
        Generator = self.env['date.range.generator']
        generator = Generator.create({
            'date_start': '%s-01-01' % self.year,
            'name_prefix': '%s/Test/Q-' % self.year,
            'type_id': self.date_range_type.id,
            'duration_count': 3,
            'unit_of_time': MONTHLY,
            'count': 4})
        generator.action_apply()

    def _create_mis_report_kpi(self):
        Account = self.env['account.account']
        type_exp = self.env.ref('account.data_account_type_expenses').id
        self.account_kpi1 = Account.create({'name': 'KPI1', 'code': 'KPI1',
                                            'user_type_id': type_exp})
        self.account_kpi2 = Account.create({'name': 'KPI2', 'code': 'KPI2',
                                            'user_type_id': type_exp})
        self.account_kpi3 = Account.create({'name': 'KPI3', 'code': 'KPI3',
                                            'user_type_id': type_exp})
        # create report
        report = self.env['mis.report'].create(dict(
            name='Test KPI',
        ))
        self.kpi1 = self.env['mis.report.kpi'].create(dict(
            report_id=report.id, name='kpi1', budgetable=True,
            description='kpi 1', expression='balp[KPI1]',
        ))
        self.kpi2 = self.env['mis.report.kpi'].create(dict(
            report_id=report.id, name='kpi2', budgetable=True,
            description='kpi 2', expression='balp[KPI2]',
        ))
        self.kpi3 = self.env['mis.report.kpi'].create(dict(
            report_id=report.id, name='kpi3', budgetable=True,
            description='kpi 3', expression='balp[KPI3]',
        ))
        return report

    def _create_budget_period_fy(self, report_id):
        BudgetPeriod = self.env['budget.period']
        budget_period = BudgetPeriod.create({
            'name': 'Budget for FY%s' % self.year,
            'report_id': report_id,
            'bm_date_from': '%s-01-01' % self.year,
            'bm_date_to': '%s-12-31' % self.year})
        return budget_period

    def _create_invoice(self, inv_type, vendor, analytic, invoice_lines):
        Invoice = self.env['account.invoice']
        with Form(Invoice.with_context(type=inv_type),
                  view='account.invoice_supplier_form') as inv:
            inv.partner_id = vendor
            for invoice_line in invoice_lines:
                with inv.invoice_line_ids.new() as line:
                    line.quantity = 1
                    line.product_id = invoice_line.get('product')
                    line.price_unit = invoice_line.get('price_unit')
                    line.account_analytic_id = analytic
        invoice = inv.save()
        return invoice

    def test_vendor_blll_budget_check(self):
        """If budget.period is set to check budget, KPI1=400.0 allocated
        - First 400.0 will used all budget allocated
        - Second 1.0 will make it exceed"""
        # Check budget
        self.budget_period.account = True
        bill1 = self._create_invoice('in_invoice', self.vendor,
                                     self.costcenter1,
                                     [{'product': self.product_kpi1,
                                       'price_unit': 400.0}])  # Equal budget
        bill1.action_invoice_open()
        # 1.0 amount will exceed the budget, and throw error
        bill2 = self._create_invoice('in_invoice', self.vendor,
                                     self.costcenter1,
                                     [{'product': self.product_kpi1,
                                       'price_unit': 1.0}])
        with self.assertRaises(UserError):
            bill2.action_invoice_open()

    def test_vendor_blll_no_budget_check(self):
        """If budget.period is not set to check budget, no budget check"""
        # No budget check
        self.budget_period.account = False
        bill1 = self._create_invoice('in_invoice', self.vendor,
                                     self.costcenter1,
                                     [{'product': self.product_kpi1,
                                       'price_unit': 100000.0}])  # big amount
        bill1.action_invoice_open()

    def test_refund_budget_check(self):
        """For refund, always not checking"""
        # First, make budget actual to exceed budget first
        self.budget_period.account = False  # No budget check first
        bill1 = self._create_invoice('in_invoice', self.vendor,
                                     self.costcenter1,
                                     [{'product': self.product_kpi1,
                                       'price_unit': 100000.0}])  # big amount
        bill1.action_invoice_open()
        # Check budget, for in_refund, force no budget check
        self.budget_period.account = True
        invoice = self._create_invoice('in_refund', self.vendor,
                                       self.costcenter1,
                                       [{'product': self.product_kpi1,
                                         'price_unit': 100.0}])
        invoice.action_invoice_open()
