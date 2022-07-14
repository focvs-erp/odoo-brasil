# -*- coding: utf-8 -*-
from collections import defaultdict
from itertools import chain
from typing import Dict, List

from odoo import api, models


class ReportIpiBook(models.AbstractModel):
    _inherit = 'report.l10n_br_eletronic_document.calculation_book'
    _name = 'report.l10n_br_eletronic_document.icms_book'
    _description = 'Livro de Apuração de ICMS'

    HEADERS = [
        "valor_bruto",
        "icms_base_calculo",
        "icms_valor",
        "isento",
        "outros",
    ]

    def generate_book_sequence(self):
        return self.env['ir.sequence'].next_by_code('l10n_br_eletronic_document.icms_book_sequence_report')

    def calculate_total_grouped_by_cfop(self, invoices) -> Dict[str, Dict[str, float]]:
        # SE O CST FOR 00, 10, 20, 51, 60, 70 SERÁ SOMADO E IRÁ PARA O CAMPO IMPOSTO CREDITADO "icms_valor"
        # SE O CST FOR 40 OU 41 SERÃO SOMADOS E ADICIONADOS NO CAMPO "isento"
        # SE O CST FOR 90 OU 50 SERÁ SOMADOS E ADICINADOS NO CAMPO "outros"
        grouped_by_cfop = super().calculate_total_grouped_by_cfop(invoices)
        invoices_lines = chain.from_iterable(
            map(lambda inv: inv.document_line_ids, invoices))

        icms_cst = {
            "icms_valor": ["00", "10", "20", "51", "60", "70"],
            "outros": ["50", "90"],
            "isento": ["40", "41"],
        }
        for invoice in invoices_lines:
            if invoice.icms_cst in icms_cst["icms_valor"]:
                grouped_by_cfop[invoice.cfop]["icms_valor"] += invoice.icms_valor

            elif invoice.icms_cst in icms_cst["outros"]:
                grouped_by_cfop[invoice.cfop]["outros"] += invoice.valor_bruto
            elif invoice.icms_cst in icms_cst["isento"]:
                grouped_by_cfop[invoice.cfop]["isento"] += invoice.valor_bruto

            grouped_by_cfop[invoice.cfop]["icms_base_calculo"] += invoice.icms_base_calculo

        return grouped_by_cfop
