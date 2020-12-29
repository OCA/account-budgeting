# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Budget Activity Purchase",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-budgeting",
    "depends": [
        "budget_control_purchase",
        "budget_activity",
    ],
    "data": [
        "views/purchase_view.xml",
    ],
    "installable": True,
    "auto_install": True,
    "maintainers": ["kittiu"],
    "development_status": "Alpha",
}
