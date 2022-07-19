# -*- coding: utf-8 -*-
from odoo import models


class IcmsBook(models.TransientModel):
    """Herda os funcionalidades padrão da model BaseCalculationBook"""
    _inherit = 'wizard.base_calculation_book'
    _name = 'wizard.icms_book'
    _description = "Responsável pelo formulário de consulta do relátorio do icms"

    def get_report(self):
        data = super().get_report()
        return self.env.ref('l10n_br_eletronic_document.icms_book_report').report_action(self, data=data)
