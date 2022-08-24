# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Iss(models.TransientModel):
    _name = "l10n_br_eletronic_document.iss_wizard"
    _description = "ISS Book Wizard"

    service_type = fields.Selection([
        ('entrada', 'Taken'),
        ('saida', 'Provided')
    ], string='Service Type')
    period_start = fields.Date(string='Start')
    period_end = fields.Date(string='End')

    def generate_report(self):
        if self.period_end < self.period_start:
            raise UserError(_('End date cannot be less than start date'))

        data = {
            'model': self._name,
            'form': {
                'service_type': self.service_type,
                'period_start': self.period_start,
                'period_end': self.period_end
            },
        }

        return self.env.ref('l10n_br_eletronic_document.report_iss').report_action(None, data=data)