# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Budget Monitoring Operating Unit",
    "summary": "Monitoring budget with Operating Unit",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-budgeting",
    "depends": [
        "budget_control",
        "budget_control_operating_unit",
        "account_operating_unit",
    ],
    "data": [
        "report/budget_monitor_report_view.xml",
    ],
    "maintainers": ["Saran440"],
    "development_status": "Alpha",
}
