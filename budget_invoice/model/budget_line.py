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

from openerp.osv import orm, fields


class BudgetLine(orm.Model):

    _name = 'budget.line'
    _inherit = 'budget.line'

    _columns = {
        'invoice_id': fields.many2one(
            'account.invoice',
            'Invoice',
            ondelete="set null"),
    }

    def invoice_create(self, cr, uid, ids, product, partner, context=None):
        invoice_obj = self.pool['account.invoice']
        invoice_line_obj = self.pool['account.invoice.line']

        invoice_data = {
            'partner_id': partner.id,
            'account_id': partner.property_account_receivable.id,
        }

        invoice_id = invoice_obj.create(cr, uid, invoice_data, context)

        for budget_line in self.browse(cr, uid, ids, context):
            invoice_line_data = {
                'name': budget_line.name or u'/',
                'price_unit': budget_line.amount,
                'invoice_id': invoice_id,
            }
            invoice_line_obj.create(cr, uid, invoice_line_data, context)

        self.write(cr, uid, ids, {'invoice_id': invoice_id}, context)

        return [invoice_id]
