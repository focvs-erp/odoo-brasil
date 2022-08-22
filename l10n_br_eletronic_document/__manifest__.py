{  # pylint: disable=C8101,C8103
    'name': 'Odoo Next - Eletronic documents',
    'description': 'Enable Eletronic Documents',
    'version': '14.0.1.0.0',
    'category': 'Localization',
    'author': 'Trustcode',
    'license': 'OEEL-1',
    'website': 'http://www.odoo-next.com,br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'l10n_br_account',
        'l10n_br_base',
        'l10n_br_base_address',
        'ax4b_invoice',
        'l10n_br_automated_payment',
    ],
    'data': [
        'data/nfe.cfop.csv',
        'data/account.cnae.csv',
        'data/account.service.type.csv',
        'data/nfe_cron.xml',
        'security/ir.model.access.csv',
        'security/eletronic_security.xml',

        'views/res_company.xml',
        'views/account_move.xml',
        'views/eletronic_document.xml',
        'views/eletronic_document_line.xml',
        'views/nfe.xml',
        'views/nfe_inutilization.xml',
        'views/base_account.xml',
        'views/fiscal_position.xml',
        'views/account_config_settings.xml',
        'views/res_partner.xml',
    

        'wizard/cancel_nfe.xml',
        'wizard/carta_correcao_eletronica.xml',
        'wizard/export_nfe.xml',
        'wizard/inutilize_nfe_numeration.xml',
        'wizard/icms_book.xml',
        'wizard/ipi_book.xml',

        'reports/danfse_sao_paulo.xml',
        'reports/danfse_florianopolis.xml',
        'reports/danfse_bh.xml',
        'reports/danfe_report.xml',
        'reports/icms_book.xml',
        'reports/ipi_book.xml',
        'reports/sequences.xml',
        'report/tax_determination_iss_report_view.xml',
        'report/iss_report_view.xml',

        'views/static_template.xml',  # CSS para relátorio de icms e ipi
    ],
}
