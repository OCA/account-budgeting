# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

from ...mis_builder.models.aep import AccountingExpressionProcessor as AEP


class MisReport(models.Model):
    _inherit = "mis.report"

    def get_kpis(self, company):
        """ By default the kpis is by account_id """
        self.ensure_one()
        kpis = self.get_kpis_by_account_id(company)
        return kpis

    def _filter_prepare_aep(self, kpis, companies, currency=None):
        aep = AEP(companies, currency, self.account_model)
        for kpi in kpis:
            for expression in kpi.expression_ids:
                if expression.name:
                    aep.parse_expr(expression.name)
        aep.done_parsing()
        return aep

    def _prepare_aep(self, companies, currency=None):
        """ Filter some kpi, performance """
        self.ensure_one()
        filter_kpi_ids = self._context.get("filter_kpi_ids", False)
        if filter_kpi_ids:
            return self._filter_prepare_aep(filter_kpi_ids, companies, currency)
        return super()._prepare_aep(companies, currency)
