from odoo import models, api


class FiscalObservation(models.Model):
    _inherit = 'eletronic.document'

    @api.onchange('fiscal_position_id')
    def _onchange_fiscal_position(self):
        self.informacoes_legais = ''
        if 'fiscal_position_id':
            self.informacoes_legais = self.fiscal_position_id.note