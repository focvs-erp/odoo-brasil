# -*- coding: utf-8 -*-

from odoo import fields, models


class ReportLivroFiscalWizard(models.TransientModel):
    _name = 'account.report_livro_fiscal_wizard'

    MODELO = [
        ('p1', 'Entry Book'),
        ('p2', 'Output Register Book'),
    ]
    book_type = fields.Selection(MODELO, string="Book Type")
    date_start = fields.Date(string="Date Start")
    date_end = fields.Date(string="Date End")

    def get_report(self):
        data = {
            'model': self._name,
            'form': {
                'book_type': self.book_type,
                'date_start': self.date_start,
                'date_end': self.date_end,
            },
        }
        return self.env.ref('l10n_br_eletronic_document.report_id').report_action(self, data=data)
