# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Budget Control Revisions",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Keep track of revised budget control",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-budgeting",
    "depends": ["base_revision", "budget_control"],
    "data": [
        "security/ir.model.access.csv",
        "views/budget_control_view.xml",
        "report/budget_monitor_revision_view.xml",
    ],
    "installable": True,
    "maintainers": ["Saran440"],
    "development_status": "Alpha",
}
