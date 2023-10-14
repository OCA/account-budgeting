#  Copyright 2022 Simone Rubino - TAKOBI
#  License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields
from odoo.models import TransientModel


class ReportBudgetLinesWizard (TransientModel):
    _name = 'account_budget_oca.budget_lines_report.wizard'
    _description = "Budget Report Wizard"

    date = fields.Date(
        default=fields.Date.today,
    )

    def generate(self):
        self.ensure_one()
        report_header = \
            self.env['account_budget_oca.budget_lines_report.header'] \
            .create({
                'date': self.date,
            })
        report_header.compute_report_data()
        return report_header.show_result()
