# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Arnaud Wüst, Guewen Baconnier
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
{"name": "Multicurrency Analytic Budget",
 "version": "1.0",
 "author": "Camptocamp",
 "category": "Generic Modules/Accounting",
 "website": "http://camptocamp.com",
 "description": """
Budget Module
=============

Features:

* Create budget, budget items and budget versions.
* Budget versions are multi currencies and multi companies.

This module is for real advanced budget use, otherwise prefer to use the
OpenERP official one.
    """,
 "complexity": "expert",
 "depends": ["base",
             "account",
             "analytic_multicurrency",
             ],
 "data": ["budget_view.xml",
          "analytic_view.xml",
          "security/ir.model.access.csv"
          ],
 "test": ["test/analytic_amount.yml"],
 "installable": True,
 "application": True,
 }
