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
            product_onchange_result = invoice_line_obj.product_id_change(
                cr, uid, [],
                product.id,
                uom_id=False,
                qty=0,
                name=budget_line.name or u'/',
                type='in_invoice',
                partner_id=partner.id,
                fposition_id=False,
                price_unit=budget_line.amount,
                currency_id=False,
                context=context,
                company_id=(budget_line.analytic_account_id and
                            budget_line.analytic_account_id.company_id.id or
                            None),
            )
            invoice_line_data = {
                'product_id': product.id,
                'account_id': product_onchange_result['value']['account_id'],
                'name': budget_line.name or u'/',
                'uos_id': product_onchange_result['value']['uos_id'],
                'price_unit': budget_line.amount,
                'invoice_id': invoice_id,
                'invoice_line_tax_id': [
                    (6, 0,
                     product_onchange_result['value']['invoice_line_tax_id'])
                ],
                'account_analytic_id': budget_line.analytic_account_id.id,
            }
            invoice_line_obj.create(cr, uid, invoice_line_data, context)

        self.write(cr, uid, ids, {'invoice_id': invoice_id}, context)

        return [invoice_id]
