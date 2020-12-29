# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Budget Transfer",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-budgeting",
    "depends": [
        "budget_control",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/budget_transfer_view.xml",
    ],
    "installable": True,
    "maintainers": ["kittiu"],
    "development_status": "Alpha",
}
