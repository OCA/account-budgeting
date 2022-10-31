# Copyright (c) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Purchase Budget OCA Validation",
    "version": "14.0.1.0.0",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "summary": "Check purchase orders against budgets",
    "license": "AGPL-3",
    "category": "Purchase",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/OCA/account-budgeting",
    "depends": ["purchase", "account_budget_oca_analytic_tag"],
    "installable": True,
    "maintainers": ["max3903"],
    "development_status": "Beta",
    "data": [
        "views/crossovered_budget_lines_view.xml",
        "views/purchase_order_view.xml",
    ],
}
