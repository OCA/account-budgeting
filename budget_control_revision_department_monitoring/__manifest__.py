# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Budget Monitoring Revision Department",
    "summary": "Monitoring budget with Revision Department",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-budgeting",
    "depends": ["budget_control_revision", "analytic_base_department"],
    "data": [
        "report/budget_monitor_revision_view.xml",
    ],
    "installable": True,
    "maintainers": ["Saran440"],
    "development_status": "Alpha",
}
