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
{"name": "Create Invoice from Budget Lines",
 "version": "1.0",
 "author": "Camptocamp,Odoo Community Association (OCA)",
 "category": "Generic Modules/Accounting",
 "website": "http://camptocamp.com",
 "description": """
Create Invoice from Budget Lines
================================

Features:

* Create automatically an Invoice from a set of Budget Lines

This module depends on the OCA module "budget", not on the Odoo core
account_budget module.
    """,
 "complexity": "normal",
 "depends": ["budget",
             ],
 "data": ['wizard/budget_line_invoice_create.xml',
          ],
 "test": [
     'test/setup_user.yml',
     'test/setup_budget.yml',
     'test/test_invoice_budget_lines.yml',
 ],
 "installable": False,
 }
