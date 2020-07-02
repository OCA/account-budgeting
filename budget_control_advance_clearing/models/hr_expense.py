# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HRExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    commitment_residual = fields.Monetary(
        string="Commitment Remaining",
        compute="_compute_commitment_residual",
        help="Pending residual for clearing commitment, in company currency",
    )
    commitment_clearing = fields.Monetary(
        string="Commitment Clearing",
        compute="_compute_commitment_residual",
        help="Pending clearing commitment, in company currency",
    )

    def _compute_commitment_residual(self):
        for sheet in self:
            if not sheet.advance_sheet_id:
                sheet.commitment_residual = 0.0
                continue
            clearing = sum(sheet.budget_move_ids.mapped('clear_advance'))
            sheet.commitment_residual = sheet.advance_sheet_residual - clearing
            sheet.commitment_clearing = clearing
            if sheet.commitment_residual < 0 or sheet.commitment_clearing < 0:
                raise ValidationError(_('Advance residual/clearing amount exception'))


class HRExpense(models.Model):
    _inherit = 'hr.expense'

    def _prepare_budget_commitment(self, account, analytic_account, doc_date,
                                   amount_currency, currency, reverse=False):
        vals = super()._prepare_budget_commitment(
            account, analytic_account, doc_date, amount_currency,
            currency, reverse=reverse)
        if not self.sheet_id.advance_sheet_id:
            return vals
        # Advance Clearing, commit only in excess of the advance amount
        self.sheet_id.invalidate_cache()
        if not reverse:  # Case commit, debit put amount into residual
            commit_amount = vals['debit']
            residual = self.sheet_id.commitment_residual
            if residual >= commit_amount:
                vals['clear_advance'] = commit_amount
                vals['debit'] = 0.0
            else:
                vals['clear_advance'] = residual
                vals['debit'] -= vals['clear_advance']
        else:  # Case uncommit, credit take amount from clearing
            commit_amount = vals['credit']
            clearing = self.sheet_id.commitment_clearing
            if clearing >= commit_amount:
                vals['clear_advance'] = -commit_amount
                vals['credit'] = 0.0
            else:
                vals['clear_advance'] = -clearing
                vals['credit'] += vals['clear_advance']
        return vals
