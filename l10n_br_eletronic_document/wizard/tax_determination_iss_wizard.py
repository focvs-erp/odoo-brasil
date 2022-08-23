# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TaxDeterminationIss(models.TransientModel):
    _name = "eletronic_document.tax_determination_iss_wizard"
    _description = "Tax Determination ISS Book Wizard"

    number = fields.Char(string='Number')
    period_start = fields.Date(string='Start')
    period_end = fields.Date(string='End')

    def generate_report(self):
        if self.period_end < self.period_start:
            raise UserError(_('End date cannot be less than start date'))

        data = {
            'model': self._name,
            'form': {
                'number': self.number,
                'period_start': self.period_start,
                'period_end': self.period_end
            },
        }

        return self.env.ref('l10n_br_eletronic_document.report_tax_determination_iss').report_action(None, data=data)
