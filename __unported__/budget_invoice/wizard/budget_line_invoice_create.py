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
from openerp.tools.translate import _


class budget_line_invoice_create(orm.TransientModel):

    _name = 'budget.line.invoice.create'
    _description = 'Create invoice from budget line'
    _columns = {
        'product_id': fields.many2one(
            'product.product',
            'Product',
            required=True),
        'partner_id': fields.many2one(
            'res.partner',
            'Partner',
            required=True),
    }

    def view_init(self, cr, uid, fields, context=None):
        """
        This magic method is called before the wizard opens. It can be used
        to check for a precondition, as it does in module hr_timesheet_invoice.
        """
        assert context['active_ids'], (
            'This wizard required a list of active_ids')

        model = self.pool[context['active_model']]

        budget_lines = model.browse(cr, uid, context['active_ids'], context)

        for budget_line in budget_lines:
            if budget_line.invoice_id:
                raise orm.except_orm(
                    _('Warning!'),
                    _("Some Budget lines are already linked to an invoice."))

    def do_create(self, cr, uid, ids, context=None):
        budget_line_obj = self.pool['budget.line']
        model_data_obj = self.pool['ir.model.data']
        action_obj = self.pool['ir.actions.act_window']

        for wiz in self.browse(cr, uid, ids, context=context):
            created_inv_ids = budget_line_obj.invoice_create(
                cr, uid, context['active_ids'], wiz.product_id, wiz.partner_id,
                context=context)

            action_id = model_data_obj.get_object_reference(
                cr, uid, 'account', 'action_invoice_tree1')[1]

            action_data = action_obj.read(cr, uid, action_id, [], context)
            action_data['domain'] = [('id', 'in', created_inv_ids)]
            action_data['name'] = _('Invoices')
            return action_data
