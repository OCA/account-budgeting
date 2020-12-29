# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast

from odoo.addons.budget_control.tests.test_budget_control import TestMisBudget


class TestBudgetControlRevision(TestMisBudget):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_01_revision_budget(self):
        """Revision budget control"""
        name_origin = "CostCenter1/%s" % self.year
        self.assertEqual(self.budget_control.state, "draft")
        self.assertTrue(self.budget_control.active)
        self.assertEqual(len(self.budget_control.item_ids), 12)
        self.assertEqual(self.budget_control.name, name_origin)
        action = self.budget_control.create_revision()
        model = action.get("res_model", False)
        domain = ast.literal_eval(action.get("domain", False))
        if model and domain:
            new_revision = self.env[model].search(domain)
            self.assertEqual(self.budget_control.state, "cancel")
            self.assertFalse(self.budget_control.active)
            self.assertEqual(len(self.budget_control.item_ids), 0)
            self.assertEqual(len(new_revision.item_ids), 12)
            self.assertEqual(new_revision.state, "draft")
            self.assertEqual(new_revision.name, "%s-01" % name_origin)
