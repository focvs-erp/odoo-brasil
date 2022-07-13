# -*- coding: utf-8 -*-
from collections import defaultdict
from itertools import chain
from typing import Dict, List

from odoo import api, models


class ReportIpiBook(models.AbstractModel):
    _inherit = 'report.l10n_br_eletronic_document.calculation_book'
    _name = 'report.l10n_br_eletronic_document.ipi_book'
    _description = 'Livro de Apuração de Ipi'

    HEADERS = [
        "valor_bruto",
        "ipi_base_calculo",
        "ipi_valor",
        "isentos",
        "outros",
    ]

    def calculate_total_by_cfop(self, invoices: List, headers: List[str]) -> Dict[str, Dict[str, float]]:
        """Realiza o calculo do totalizador por cfop com a condição do tipo de imposto por cst"""
        # Entrada: 00, 01, 02, 03, 04, 05, 49
        # ipi: 00, 01,
        # outros: 49, 03
        # isentoss: 04, 05, 02

        # Saida: 50, 51, 52, 53, 54, 55, 99
        # ipi: 50, 51
        # outros: 53, 54, 55
        # isentoss: 52, 99
        grouped_by_cfop = defaultdict(lambda: dict.fromkeys(headers, 0.0))
        invoices_lines = chain.from_iterable(
            map(lambda item: item.document_line_ids, invoices))

        ipi_cst = {
            "ipi_valor": ['00', '01', '50', '51'],
            "outros": ['03', '49', '53', '54', '55'],
            "isentos": ['02', '04', '05', '52', '99'],
        }

        for invoice in invoices_lines:
            if invoice.ipi_cst in ipi_cst["ipi_valor"]:
                grouped_by_cfop[invoice.cfop]["ipi_valor"] += invoice.ipi_valor
            elif invoice.ipi_cst in ipi_cst["outros"]:
                grouped_by_cfop[invoice.cfop]["outros"] += invoice.valor_bruto
            elif invoice.ipi_cst in ipi_cst["isentos"]:
                grouped_by_cfop[invoice.cfop]["isentos"] += invoice.valor_bruto

            grouped_by_cfop[invoice.cfop]["valor_bruto"] += invoice.valor_bruto
            grouped_by_cfop[invoice.cfop]["ipi_base_calculo"] += invoice.ipi_base_calculo

        return grouped_by_cfop
