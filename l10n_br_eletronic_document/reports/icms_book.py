# -*- coding: utf-8 -*-

from collections import OrderedDict, defaultdict
from datetime import date, datetime
from functools import reduce
from itertools import chain, groupby, product
from operator import attrgetter
from typing import AnyStr, Dict, List

from odoo import api, fields, models
# from odoo.exceptions import ValidationError
from pytz import timezone

TIMEZONE = timezone('America/Sao_Paulo')
HEADERS = ['valor_bruto', 'icms_base_calculo', 'icms_valor', 'ipi_valor']


class ReportIcmsBook(models.AbstractModel):
    _name = 'report.l10n_br_eletronic_document.icms_book'
    _description = 'Livro de Apuração de ICMS'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        docs = self.env['eletronic.document'].search([])

        return {
            'docs': docs,
            'date_start': date.fromisoformat(date_start),
            'date_end': date.fromisoformat(date_end),
            # 'total_value': self.calculate_total_values(
            #     invoices=docs_invoices, headers=HEADERS),
            # 'total_by_cfop': self.calculate_total_by_cfop(
            #     invoices=docs_invoices, headers=HEADERS),
            # 'calculate_total_by_cfop_and_aliquot': self.calculate_total_by_cfop_and_aliquot(
            #     invoices=docs_invoices, headers=HEADERS
            # ),
        }
