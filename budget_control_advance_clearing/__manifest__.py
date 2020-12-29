# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Budget Control on Expense extension on Advance/Clearing",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-budgeting",
    "depends": [
        "budget_control_expense",
        "hr_expense_advance_clearing",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/budget_period_view.xml",
        "views/hr_expense_view.xml",
    ],
    "installable": True,
    "auto_install": True,
    "maintainers": ["kittiu"],
    "development_status": "Alpha",
}
