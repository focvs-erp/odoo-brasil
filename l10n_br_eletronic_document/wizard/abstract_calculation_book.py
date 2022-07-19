# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import UserError


class BaseCalculationBook(models.TransientModel):
    _name = 'wizard.base_calculation_book'
    _description = "Responsável pelo form de consulta para livros de apuração"

    date_start = fields.Date(string="Date Start")
    date_end = fields.Date(string="Date End")

    def validate_dates_are_in_same_period(self):
        if (self.date_start.month != self.date_end.month or self.date_start.year != self.date_end.year):
            raise UserError(
                'Both dates must be in the same period of month and year!')

    def get_report(self):
        """Metodo responsavel por enviar os campos do formulário para o relátorio na abstractmodel"""
        self.validate_dates_are_in_same_period()
        data = {
            'model': self._name,
            'form': {
                'date_start': self.date_start,
                'date_end': self.date_end,
            },
        }
        return data
