# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Account Budget OCA Analytic Tag",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "summary": "This module allows you to select an analytic tag on the budget"
    " line and report the consumed budget using that tag.",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/OCA/account-budgeting",
    "category": "Accounting",
    "depends": ["account_budget_oca"],
    "data": [
        "views/account_budget_views.xml",
    ],
    "installable": True,
    "maintainers": ["max3903"],
}
