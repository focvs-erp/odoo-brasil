# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import date
from itertools import chain, product
from typing import Dict, Iterable, List, TypeVar
from odoo import api, models


EletronicDocument = TypeVar('EletronicDocument')


class ReportCalculationBook(models.AbstractModel):
    """
    Este modelo é usado como base para realizar os calculos dos livros de apuração IPI e ICMS.
    icms_book
    ipi_book
    """
    _name = 'report.l10n_br_eletronic_document.calculation_book'
    _description = 'Modelo Base para uso em livros de apuração e Cálculos no Odoo'

    HEADERS = [
        "valor_bruto",
        "isentos",
        "outros",
    ]

    CST: Dict[str, List[str]] = {}

    def generate_book_sequence(self):
        """Função responsavel por criar o sequencial que será usado no livro de apuração do Ipi
            return self.env['ir.sequence].next_by_code('nome_ou_id_do_xml_sequence')
        """
        return

    def get_invoices_by_operation_type(self,
                                       docs: List[object],
                                       operation_type: str) -> Iterable[int]:
        """
            Retorna se a nota é de entrada ou de saida.
            :param: str operation_type: Recebe 'entrada' para notas de entrada ou 'saida' para notas de saida.
        """
        return docs.filtered(lambda item: item.tipo_operacao == operation_type)

    def calculate_values_grouped_by_cfop_type(self,
                                  invoices: Dict[str, Dict[str, float]],
                                  ) -> Dict[str, Dict[str, float]]:
        """Realiza o agrupador do cfop por tipo de cfop, Estado, Fora do estado e Exterior."""
        grouped_by_cfop = defaultdict(lambda: dict.fromkeys(self.HEADERS, 0.0))

        for (cfop, invoice), header in product(invoices.items(), self.HEADERS):
            grouped_by_cfop[f"{cfop[:1]}000"][header] += invoice.get(
                header, 0.0)

        return grouped_by_cfop

    def calculate_total_for_all_values(self,
                                           invoices: Dict[str, Dict[str, float]]
                                           ) -> Dict[str, float]:
        """Realizada a somatória geral para cada coluna/atributo do relátorio"""
        grouped_by_cfop = defaultdict(float)

        for invoice, header in product(invoices.values(), self.HEADERS):
            grouped_by_cfop[header] += invoice.get(header, 0.0)

        return grouped_by_cfop

    def calculate_total_grouped_by_cfop(self, invoices: List[EletronicDocument]) -> Dict[str, Dict[str, float]]:
        """Este metodo implementa a base para gerar os calculos do produto por cfop.
            porem falta a funcionalidade para que seja calculado o cst onde deve adicionar se é ipi, icms, isento ou outros."""

        grouped_by_cfop = defaultdict(lambda: dict.fromkeys(self.HEADERS, 0.0))
        invoices_lines = chain.from_iterable(
            map(lambda item: item.document_line_ids, invoices))

        for invoice in invoices_lines:
            grouped_by_cfop[invoice.cfop]["valor_bruto"] += invoice.valor_bruto

        return grouped_by_cfop

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
             ('numero', '!=', False)], order='numero')

        entry_notes_by_cfop = self.calculate_total_grouped_by_cfop(
            invoices=self.get_invoices_by_operation_type(docs=docs, operation_type='entrada'))

        exit_notes_by_cfop = self.calculate_total_grouped_by_cfop(
            invoices=self.get_invoices_by_operation_type(docs=docs, operation_type='saida'))

        return {
            'company': self.env.user.company_id,
            'date_start': date.fromisoformat(date_start),
            'date_end': date.fromisoformat(date_end),
            'book_sequence': self.generate_book_sequence() or 'X0001',
            # Notas de Entrada
            'entry_notes_by_cfop': entry_notes_by_cfop,
            'grouped_by_cfop_type_entry_notes': self.calculate_values_grouped_by_cfop_type(invoices=entry_notes_by_cfop),
            'total_entry_notes': self.calculate_total_for_all_values(invoices=entry_notes_by_cfop),
            # Notas de Saída
            'exit_notes_by_cfop': exit_notes_by_cfop,
            'grouped_by_cfop_type_exit_notes': self.calculate_values_grouped_by_cfop_type(invoices=exit_notes_by_cfop),
            'total_exit_notes': self.calculate_total_for_all_values(invoices=exit_notes_by_cfop),
        }
