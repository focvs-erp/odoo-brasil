# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ReportTaxDeterminationISS(models.AbstractModel):
    _name = "report.eletronic_document.tax_determination_iss"
    _description = "Tax Determination ISS"

    def calculate_total(self, docs):
        values = {
            'note_value': 0,
            'deductions': 0,
            'iss_base': 0,
            'iss_value': 0
        }

        for item in docs:
            values['note_value'] += item.valor_final
            values['deductions'] += item.iss_valor_retencao
            values['iss_value'] += item.iss_valor

        values['iss_base'] = values['note_value']

        return values

    def verify_fields(self, docs):
        for item in docs:
            if item.valor_final == '': item.valor_final = 0
            if item.iss_valor == '': item.iss_valor = 0
            if item.iss_valor_retencao == '': item.iss_valor_retencao = 0

    @api.model
    def _get_report_values(self, docids, data=None):
        period_end = data['form']['period_end']
        period_start = data['form']['period_start']
        number = data['form']['number']

        domain = [('document_template_id.model_code','=', 'nfse'), ('data_emissao', '>=', period_start), ('data_emissao', '<=', period_end)]

        if number:
            domain.append(('numero','=', number)) 
        
        docs = self.env['eletronic.document'].search(domain)

            
        self.verify_fields(docs)

        return {
            'number': number,
            'period_start': '{2}/{1}/{0}'.format(*period_start.split('-')),
            'period_end': '{2}/{1}/{0}'.format(*period_end.split('-')),
            'total': self.calculate_total(docs),
            'docs': docs
        }
