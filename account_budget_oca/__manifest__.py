# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Budgets Management",
    "version": "13.0.1.0.0",
    "category": "Accounting",
    "license": "LGPL-3",
    "author": "Odoo S.A., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-budgeting",
    "depends": ["account"],
    "excludes": ["account_budget"],
    "data": [
        "security/ir.model.access.csv",
        "security/account_budget_security.xml",
        "views/account_analytic_account_views.xml",
        "views/account_budget_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": ["data/account_budget_demo.xml"],
}
