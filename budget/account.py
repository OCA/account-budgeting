# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Arnaud Wüst
#    Copyright 2009-2013 Camptocamp SA
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
from openerp.osv import orm


class account_period(orm.Model):

    """ add new methods to the account_period base object """
    _inherit = 'account.period'

    def _get_next_periods(self, cr, uid, start_period,
                          periods_nbr, context=None):
        """ return a list of browse record periods that follow the
        "start_period" for the given version.

        periods_nbr is the limit of periods to return"""
        period_obj = self.pool.get('account.period')
        period_ids = period_obj.next(cr, uid, start_period,
                                     periods_nbr,
                                     context=context)
        if not period_ids:
            return None
        return period_obj.browse(cr, uid, period_ids, context=context)

    def _get_previous_period(self, cr, uid, period, context=None):
        """ return the period that preceed the one given in param.
            return None if there is no preceeding period defined """
        period_obj = self.pool.get('account.period')
        ids = period_obj.search(cr, uid,
                                [('date_stop', '<', period.date_start)],
                                order="date_start DESC",
                                limit=1,
                                context=context)
        if not ids:
            return None
        return period_obj.browse(cr, uid, ids[0], context)
