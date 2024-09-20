#  Copyright 2022 Simone Rubino - TAKOBI
#  License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import Form
from .common import TestAccountBudgetCommon


class TestLinesReport (TestAccountBudgetCommon):

    def test_report_theoretical_amount(self):
        """
        The report shows the budget lines amounts in a specified date.
        """
        # Clean any other budget line that might concur in the report
        self.env['crossovered.budget.lines'].search([]).unlink()
        # Arrange: Create a budget of 1000 for the next 10 days
        date_from = fields.Date.today() + relativedelta(days=1)
        date_to = date_from + relativedelta(days=10)
        budget_form = Form(self.env['crossovered.budget'])
        budget_form.name = "Test budget"
        budget_form.date_from = date_from
        budget_form.date_to = date_to
        with budget_form.crossovered_budget_line_ids.new() as line:
            line.planned_amount = 1000
            line.general_budget_id = self.account_budget_post_sales0
        budget = budget_form.save()
        # pre-condition: Right now, the theoretical amount is 0
        budget_lines = budget.mapped('crossovered_budget_line_ids')
        budget_theoretical_amount = sum(budget_lines.mapped('theoretical_amount'))
        self.assertEqual(budget_theoretical_amount, 0)

        # Act: Create the report for 5 days from now
        wizard_form = Form(self.env['account_budget_oca.budget_lines_report.wizard'])
        wizard_form.date = date_from + relativedelta(days=5)
        wizard = wizard_form.save()
        report_action = wizard.generate()
        report_lines_model = report_action.get('res_model')
        report_lines_domain = report_action.get('domain')
        report_lines = self.env[report_lines_model].search(report_lines_domain)

        # Assert: The report show that the theoretical amount is 500
        report_theoretical_amount = sum(report_lines.mapped('theoretical_amount'))
        self.assertEqual(report_theoretical_amount, 500)
