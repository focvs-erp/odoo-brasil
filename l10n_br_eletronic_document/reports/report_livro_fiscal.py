# -*- coding: utf-8 -*-

from collections import OrderedDict, defaultdict
from datetime import date, datetime
from itertools import chain, groupby, product
from operator import attrgetter
from typing import Dict, List
from odoo import api, models
from pytz import timezone

TIMEZONE = timezone('America/Sao_Paulo')
HEADERS = ['valor_bruto', 'icms_base_calculo', 'icms_valor', 'ipi_valor']


class ReportLivroFiscal(models.AbstractModel):
    _name = 'report.eletronic_document.report_livro_fiscal'
    _description = 'Livro Fiscal'

    def filter_lines_in_invoices(self, docs: List[object]) -> List[object]:
        '''Retorna lista de notas que tem ao menos algum produto cadastrado'''
        return [invoice for invoice in docs if invoice.document_line_ids.exists()]

    def get_cfop_type(self, docs: List[object], book_type: str) -> List[int]:
        '''Valida se o produto está com cfop preenchido'''
        cfops = {'p1': ['1', '2', '3'], 'p2': ['5', '6', '7']}
        invoices_with_cfop = []
        for invoice in self.filter_lines_in_invoices(docs):
            for line in invoice.document_line_ids:
                if line.cfop and line.cfop[0] in cfops[book_type]:
                    invoices_with_cfop.append(invoice.id)
        return invoices_with_cfop

    def calculate_total_by_cfop(self, invoices: List[object], headers: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        '''Agrupa as notas com o mesmo CFOP'''
        grouped_by_cfop: Dict[str, Dict[str, float]] = defaultdict(
            lambda v=0.0: dict.fromkeys(headers, v))
        for invoice in invoices:
            for item in product(invoice.document_line_ids, headers):
                grouped_by_cfop[item[0].cfop][item[1]] += getattr(item[0], item[1], 0.0)
        return grouped_by_cfop

    def calculate_total_values(self, invoices: List[object], headers: Dict[str, float]) -> Dict[str, float]:
        '''Realiza a soma total de todas as notas. produtos'''
        total_values: Dict[str, float] = defaultdict(float)
        for invoice in invoices:
            for item in product(invoice.document_line_ids, headers):
                total_values[item[1]] += getattr(item[0], item[1], 0.0)
        return total_values

    def calculate_grouped_values_at_lines(self, line_ids: List[object], headers: Dict[str, float]) -> Dict[str, float]:
        '''Recebe a lista contendo as linhas do invoices sorteada por cfop e aliquota, para realizar a soma dos totais'''
        total_values: Dict[str, float] = defaultdict(float)
        # free = isento, others = outros
        cst = {'free': '41', 'others': '40'}
        for line in line_ids:
            if line.icms_cst == cst['free']:
                total_values['free'] += getattr(line, 'valor_bruto', 0.0)
            if line.icms_cst == cst['others']:
                total_values['others'] += getattr(line, 'valor_bruto', 0.0)

            for header in headers:
                total_values[header] += getattr(line, header, 0.0)
        return total_values

    def calculate_total_by_cfop_and_aliquot(self, invoices: List[object], headers: List[str]) -> Dict[str, Dict[str, float]]:
        '''Recebe a lista dos calculos por linha para cada tipo de aliquota e agrupa por CFOP'''
        res = []
        invoices_lines = chain.from_iterable(
            [item.document_line_ids for item in invoices])
        key = attrgetter('cfop', 'icms_aliquota')
        group = groupby(sorted(invoices_lines, key=key), key=key)
        for k, g in group:
            temp_dict = OrderedDict(zip(["cfop", "icms_aliquota"], k))
            temp_dict['group'] = self.calculate_grouped_values_at_lines(
                line_ids=list(g), headers=headers)
            res.append(temp_dict)
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        book_type = data['form']['book_type']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']

        docs = self.env['eletronic.document'].search(
            ['&', ('data_emissao', '>=', date_start),
             ('data_emissao', '<=', date_end),
             ('company_id', '=', self.env.user.company_id.id),
             ('numero', '!=', False)],
            order='data_emissao')
        docs_invoices = docs.browse(set(self.get_cfop_type(
            docs=docs, book_type=book_type))
        )
        return {
            'doc_ids': docs_invoices.ids,
            'docs': docs_invoices,
            'doc_model': data['model'],
            'data': data,
            'date': datetime.now(tz=TIMEZONE).strftime('%d/%m/%Y - %H:%M:%S'),
            'date_start': date.fromisoformat(date_start),
            'date_end': date.fromisoformat(date_end),
            'book_type': book_type,
            'total_value': self.calculate_total_values(
                invoices=docs_invoices, headers=HEADERS),
            'total_by_cfop': self.calculate_total_by_cfop(
                invoices=docs_invoices, headers=HEADERS),
            'calculate_total_by_cfop_and_aliquot': self.calculate_total_by_cfop_and_aliquot(
                invoices=docs_invoices, headers=HEADERS
            ),
        }
