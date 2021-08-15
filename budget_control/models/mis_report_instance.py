# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    def _get_context_filter_matrix(self):
        ctx = self.env.context.copy()
        if ctx.get("filter_analytic_ids"):
            ctx["mis_report_filters"] = ctx.get("mis_report_filters", {})
            ctx["mis_report_filters"]["analytic_account_id"] = {
                "value": ctx["filter_analytic_ids"],
                "operator": "all",
            }
        if ctx.get("filter_period_date_to") and ctx.get("filter_period_date_from"):
            ctx["mis_report_filters"]["date"] = {
                "value": [
                    ctx["filter_period_date_from"],
                    ctx["filter_period_date_to"],
                ],
                "operator": "between",  # add new operator between
            }
        else:
            if ctx.get("filter_period_date_from"):
                ctx["mis_report_filters"]["date"] = {
                    "value": ctx["filter_period_date_from"],
                    "operator": ">=",
                }
            elif ctx.get("filter_period_date_to"):
                ctx["mis_report_filters"]["date"] = {
                    "value": ctx["filter_period_date_to"],
                    "operator": "<=",
                }
        return ctx

    def _compute_matrix(self):
        """ Add possible filter_analytic_ids to compute """
        ctx = self._get_context_filter_matrix()
        return super(MisReportInstance, self.with_context(ctx))._compute_matrix()


class MisReportInstancePeriod(models.Model):
    _inherit = "mis.report.instance.period"

    def search_neutralize(self, dom, filters):
        if dom[1] == "between":
            filters.append((dom[0], ">=", dom[2][0]))
            filters.append((dom[0], "<=", dom[2][1]))
            return (1, "=", 1)
        return dom

    @api.model
    def _get_filter_domain_from_context(self):
        filters = super()._get_filter_domain_from_context()
        filters = [
            isinstance(dom, tuple) and self.search_neutralize(dom, filters) or dom
            for dom in filters
        ]
        return filters
