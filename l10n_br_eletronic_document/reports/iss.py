# -*- coding: utf-8 -*-

from odoo import models, api


class ReportIss(models.AbstractModel):
    _name = "report.l10n_br_eletronic_document.iss"
    _description = "Iss"

    def calculate_total(self, docs):
        values = {
            'total_value': 0,
            'total_own': 0,
            'total_retained': 0
        }

        for item in docs:
            values['total_value'] += item.valor_final
            values['total_own'] += item.iss_valor
            values['total_retained'] += item.iss_valor_retencao

        return values

    def verify_fields(self, docs):
        for item in docs:
            if item.valor_final == '':
                item.valor_final = 0
            if item.iss_valor == '':
                item.iss_valor = 0
            if item.iss_valor_retencao == '':
                item.iss_valor_retencao = 0

    @api.model
    def _get_report_values(self, docids, data=None):
        service_type = data['form']['service_type']
        period_start = data['form']['period_start']
        period_end = data['form']['period_end']
        docs = self.env['eletronic.document'].search([('document_template_id.model_code', '=', 'nfse'), ('data_emissao', '>=', period_start), ('data_emissao', '<=', period_end), ('tipo_operacao', '=', service_type)])
        self.verify_fields(docs)
        return {
            'service_type': service_type,
            'period_start': '{2}/{1}/{0}'.format(*period_start.split('-')),
            'period_end': '{2}/{1}/{0}'.format(*period_end.split('-')),
            'total': self.calculate_total(docs),
            'docs': docs
        }
