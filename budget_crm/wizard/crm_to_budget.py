# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Leonardo Pistone
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import datetime as dt
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
import calendar

from openerp.osv import orm
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class CrmToBudgetWizard(orm.TransientModel):

    _name = 'crm.to.budget.wizard'

    def _line_dates(self, start_date, count):
        for date in rrule(MONTHLY, count=count, bymonthday=1,
                          dtstart=start_date):
            yield (date, date + relativedelta(months=1, days=-1))

    def do_compute(self, cr, uid, ids, context=None):
        lead_obj = self.pool['crm.lead']
        budget_line_obj = self.pool['budget.line']

        lead_ids = context['active_ids']

        for lead in lead_obj.browse(cr, uid, lead_ids, context):

            if lead.budget_line_ids:
                budget_line_obj.unlink(cr, uid, [
                    line.id for line in lead.budget_line_ids
                ], context=context)

            if not lead.budget_item_id:
                # we do not raise here because we do not want to revert the
                # deletion of old budget lines
                continue

            if not lead.date_deadline:
                raise orm.except_orm(_(u'Error'),
                                     _(u'The Expected Date must be set'))

            if not lead.months:
                raise orm.except_orm(
                    _(u'Error'),
                    _(u'The Duration in months must be set'))

            if not lead.planned_revenue:
                raise orm.except_orm(
                    _(u'Error'),
                    _(u'The Expected Revenue must be set'))

            if not lead.analytic_account_id:
                raise orm.except_orm(
                    _(u'Error'),
                    _(u'The Analytic Account must be set'))

            version = lead.company_id.budget_version_id
            if not version:
                raise orm.except_orm(
                    _(u'Error'),
                    _(u'The budget version must be set in the company'))

            deadline = dt.datetime.strptime(lead.date_deadline,
                                            DATE_FORMAT)
            budget_lines = []
            for date_start, date_stop in self._line_dates(deadline,
                                                          lead.months):
                budget_lines.append((0, 0, {
                    'name': u'{0} - {1} {2}'.format(
                        lead.name,
                        _(calendar.month_name[date_start.month]),
                        date_start.year),
                    'date_start': date_start,
                    'date_stop': date_stop,
                    'analytic_account_id': lead.analytic_account_id.id,
                    'budget_item_id': lead.budget_item_id.id,
                    'amount': lead.planned_revenue / lead.months,
                    'currency_id': lead.currency_id.id,
                    'budget_version_id': version.id,
                }))

            lead.write({'budget_line_ids': budget_lines})
