# -*- coding: utf-8 -*-

from datetime import date, datetime
from odoo import api, fields, models
from traitlets import default


class IcmsBook(models.TransientModel):
    _name = 'wizard.icms_book'
    _description = "Responsável pelo formulário de consulta do relátorio do icms"

    date_start = fields.Date(string="Date Start")
    date_end = fields.Date(string="Date End")

    def get_report(self):
        data = {
            'model': self._name,
            'form': {
                'date_start': self.date_start,
                'date_end': self.date_end,
            },
        }

        return self.env.ref('l10n_br_eletronic_document.icms_book_report').report_action(self, data=data)
