# -*- coding: utf-8 -*-
import locale
from collections import defaultdict
from datetime import date
from itertools import chain, groupby, product
from operator import attrgetter
from typing import Dict, List
from operator import add

from odoo import api, models
from pytz import timezone

TIMEZONE = timezone('America/Sao_Paulo')
HEADERS = [
    "valor_bruto",
    "icms_base_calculo",
    "icms_valor",
    "isento",
    "outros",
]


class ReportIcmsBook(models.AbstractModel):
    _name = 'report.l10n_br_eletronic_document.icms_book'
    _description = 'Livro de Apuração de ICMS'

    def generate_book_sequence(self):
        """Função responsavel por criar o sequencial que será usado no livro de apuração do ICMS"""
        # sequence = self.env['ir.sequence'].search(
        #     [('code', '=', 'l10n_br_eletronic_document.icms_book_sequence')]).next_by_id()
        # return sequence
        return self.env['ir.sequence'].next_by_code('l10n_br_eletronic_document.icms_book_sequence')

    def filter_lines_in_invoices(self, docs):
        '''Retorna lista de notas que tem ao menos algum produto cadastrado'''
        return [invoice for invoice in docs if invoice.document_line_ids.exists()]

    def get_invoices_with_cfop(self, docs: list, book_type: str):
        '''Valida se o produto está com cfop preenchido'''
        cfops = {'p1': ['1', '2', '3'], 'p2': ['5', '6', '7']}
        invoices_with_cfop = []

        for invoice in self.filter_lines_in_invoices(docs):
            for line in invoice.document_line_ids:
                if line.cfop and line.cfop[0] in cfops[book_type]:
                    invoices_with_cfop.append(invoice.id)

        return invoices_with_cfop

    def group_values_by_cfop_type(self, by_cfop: Dict[str, Dict[str, float]], headers: List[str]) -> Dict[str, Dict[str, float]]:
        """Realiza o agrupador do cfop por tipo de entrada"""
        grouped_by_cfop = defaultdict(lambda: dict.fromkeys(headers, 0.0))
        for cfop, values in by_cfop.items():
            grouped_by_cfop[cfop[:1]]["valor_bruto"] += values["valor_bruto"]
            grouped_by_cfop[cfop[:1]]["icms_valor"] += values["icms_valor"]
            grouped_by_cfop[cfop[:1]]["outros"] += values["outros"]
            grouped_by_cfop[cfop[:1]]["isento"] += values["isento"]
            grouped_by_cfop[cfop[:1]]["icms_base_calculo"] += values["icms_base_calculo"]

        return dict(grouped_by_cfop)

    def calculte_total(self, by_cfop: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Calcula total geral para os items da nota fiscal"""
        grouped_by_cfop = defaultdict(float)

        for value in by_cfop.values():
            grouped_by_cfop["valor_bruto"] += value["valor_bruto"]
            grouped_by_cfop["icms_base_calculo"] += value["icms_base_calculo"]
            grouped_by_cfop["icms_valor"] += value["icms_valor"]
            grouped_by_cfop["outros"] += value["outros"]
            grouped_by_cfop["isento"] += value["isento"]

        return dict(grouped_by_cfop)

    def calculate_total_by_cfop(self, invoices: List, headers: List[str]):
        """Realiza o calculo do totalizador por cfop com a condição do tipo de imposto por cst"""
        # SE O CST FOR 00, 10, 20, 51, 60, 70 SERÁ SOMADO E IRÁ PARA O CAMPO IMPOSTO CREDITADO "icms_valor"
        # SE O CST FOR 40 OU 41 SERÃO SOMADOS E ADICIONADOS NO CAMPO "isento"
        # SE O CST FOR 90 OU 50 SERÁ SOMADOS E ADICINADOS NO CAMPO "outros"
        grouped_by_cfop = defaultdict(lambda: dict.fromkeys(headers, 0.0))
        invoices_lines = chain.from_iterable(
            [item.document_line_ids for item in invoices])

        icms_cst = {
            "icms": ["00", "10", "20", "51", "60", "70"],
            "outros": ["50", "90"],
            "isento": ["40", "41"],
        }

        for invoice in invoices_lines:
            if invoice.icms_cst in icms_cst["icms"]:
                grouped_by_cfop[invoice.cfop]["icms_valor"] += invoice.icms_valor
            elif invoice.icms_cst in icms_cst["outros"]:
                grouped_by_cfop[invoice.cfop]["outros"] += invoice.valor_bruto
            elif invoice.icms_cst in icms_cst["isento"]:
                grouped_by_cfop[invoice.cfop]["isento"] += invoice.valor_bruto

            grouped_by_cfop[invoice.cfop]["valor_bruto"] += invoice.valor_bruto
            grouped_by_cfop[invoice.cfop]["icms_base_calculo"] += invoice.icms_base_calculo

        return dict(grouped_by_cfop)

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']

        docs = self.env['eletronic.document'].search(
            ['&', ('data_emissao', '>=', date_start),
             ('data_emissao', '<=', date_end),
                 ('code_related', '=', '55'),
                ('company_id', '=', self.env.user.company_id.id),
                ('numero', '!=', False)],
            order='data_emissao')

        entry_notes_by_cfop = self.calculate_total_by_cfop(
            invoices=docs.browse(set(self.get_invoices_with_cfop(docs=docs, book_type='p1'))), 
            headers=HEADERS)
        exit_notes_by_cfop = self.calculate_total_by_cfop(
            invoices=docs.browse(set(self.get_invoices_with_cfop(docs=docs, book_type='p2'))), 
            headers=HEADERS)


        return {
            'docs': docs,
            'date_start': date.fromisoformat(date_start),
            'date_end': date.fromisoformat(date_end),
            'book_sequence': self.generate_book_sequence() or "X00001",
            # Entry notes
            'entry_notes_by_cfop': entry_notes_by_cfop,
            'grouped_by_cfop_type_entry_notes': self.group_values_by_cfop_type(by_cfop=entry_notes_by_cfop, headers=HEADERS),
            'total_entry_notes': self.calculte_total(by_cfop=entry_notes_by_cfop),
            # Exit notes
            'exit_notes_by_cfop': exit_notes_by_cfop,
            'grouped_by_cfop_type_exit_notes': self.group_values_by_cfop_type(by_cfop=exit_notes_by_cfop, headers=HEADERS),
            'total_exit_notes': self.calculte_total(by_cfop=exit_notes_by_cfop),
        }
