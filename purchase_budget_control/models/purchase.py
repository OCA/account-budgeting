# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def get_kpi_value(self, kpi_matrix, kpi, period):
        for row in kpi_matrix.iter_rows():
            if row.kpi == kpi:
                for cell in row.iter_cells():
                    if cell.subcol.col.key == period.id:
                        return cell.val or 0.0
        return 0.0

    @api.multi
    def button_confirm(self):
        res = super().button_confirm()
        # From

        company = self.env.ref('base.main_company')
        report = self.env.ref('mis_builder_demo.mis_report_expenses')
        report_instance = self.env.ref(
            'mis_builder_demo.mis_report_instance_expenses')
        print(report_instance.compute())
        kpi_matrix = report_instance._compute_matrix()
        print(self.get_val(kpi_matrix))
        return res
