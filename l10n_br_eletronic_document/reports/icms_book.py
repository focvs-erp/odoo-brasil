# -*- coding: utf-8 -*-
from email import header
import locale
from collections import defaultdict
from datetime import date
from itertools import chain, groupby, product
from operator import attrgetter
from typing import Dict, Iterable, List, Set
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

    def generate_book_sequence(self, sequence_name: str):
        """Função responsavel por criar o sequencial que será usado no livro de apuração do ICMS"""
        return self.env['ir.sequence'].next_by_code(sequence_name)

    def get_invoices_by_operation_type(self, docs: List[object], book_type: str) -> Iterable[int]:
        """
            Retorna se a nota é de entrada ou de saida.
            :param: str book_type: Recebe 'entrada' para notas de entrada ou 'saida' para notas de saida.
        """
        return docs.filtered(lambda item: item.tipo_operacao == book_type)

    def group_values_by_cfop_type(self, by_cfop: Dict[str, Dict[str, float]], headers: List[str]) -> Dict[str, Dict[str, float]]:
        """Realiza o agrupador do cfop por tipo de cfop, Estado, Fora do estado e Exterior."""
        grouped_by_cfop = defaultdict(lambda: dict.fromkeys(headers, 0.0))

        for (cfop, invoice), header in product(by_cfop.items(), headers):
            grouped_by_cfop[f"{cfop[:1]}000"][header] += invoice.get(
                header, 0.0)

        return dict(grouped_by_cfop)

    def calculate_total_for_each_attribute(self, by_cfop: Dict[str, Dict[str, float]], headers: List[str]) -> Dict[str, float]:
        """Compute total geral para os items da nota fiscal"""
        grouped_by_cfop = defaultdict(float)

        for invoice, header in product(by_cfop.values(), headers):
            grouped_by_cfop[header] += invoice.get(header, 0.0)

        return dict(grouped_by_cfop)

    def calculate_total_by_cfop(self, invoices: List, headers: List[str]) -> Dict[str, Dict[str, float]]:
        """Realiza o calculo do totalizador por cfop com a condição do tipo de imposto por cst"""
        # SE O CST FOR 00, 10, 20, 51, 60, 70 SERÁ SOMADO E IRÁ PARA O CAMPO IMPOSTO CREDITADO "icms_valor"
        # SE O CST FOR 40 OU 41 SERÃO SOMADOS E ADICIONADOS NO CAMPO "isento"
        # SE O CST FOR 90 OU 50 SERÁ SOMADOS E ADICINADOS NO CAMPO "outros"
        grouped_by_cfop = defaultdict(lambda: dict.fromkeys(headers, 0.0))
        invoices_lines = chain.from_iterable(
            map(lambda item: item.document_line_ids, invoices))

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
             ('codigo_retorno', '=', '100'),
             ('company_id', '=', self.env.user.company_id.id),
             ('numero', '!=', False)],
            order='data_emissao')

        entry_notes_by_cfop = self.calculate_total_by_cfop(
            invoices=self.get_invoices_by_operation_type(docs=docs, book_type='entrada'), headers=HEADERS)
            
        exit_notes_by_cfop = self.calculate_total_by_cfop(
            invoices=self.get_invoices_by_operation_type(docs=docs, book_type='saida'), headers=HEADERS)

        return {
            'docs': docs,
            'date_start': date.fromisoformat(date_start),
            'date_end': date.fromisoformat(date_end),
            'book_sequence': self.generate_book_sequence(sequence_name='l10n_br_eletronic_document.icms_book_sequence') or "X00001",
            # Entry notes
            'entry_notes_by_cfop': entry_notes_by_cfop,
            'grouped_by_cfop_type_entry_notes': self.group_values_by_cfop_type(by_cfop=entry_notes_by_cfop, headers=HEADERS),
            'total_entry_notes': self.calculate_total_for_each_attribute(by_cfop=entry_notes_by_cfop, headers=HEADERS),
            # Exit notes
            'exit_notes_by_cfop': exit_notes_by_cfop,
            'grouped_by_cfop_type_exit_notes': self.group_values_by_cfop_type(by_cfop=exit_notes_by_cfop, headers=HEADERS),
            'total_exit_notes': self.calculate_total_for_each_attribute(by_cfop=exit_notes_by_cfop, headers=HEADERS),
        }
