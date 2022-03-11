from odoo import http, tools, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class BrWebsiteMyAccount(CustomerPortal):
    def update_client(self, post):
        responsible = ['name_responsible', 'email_responsible', 'phone_responsible', 
        'name_responsible_for_license', 'email_responsible_for_license',
         'phone_responsible_for_license', 'checkbox_responsible_license']

        if len(post) != 0:
            partner = request.env['res.users'].search([('id', '=', request.uid)]).partner_id.id
            request.env['res.partner'].write_partner_contact(partner, post, 'checkbox_responsible_license')
            
            for i in responsible:
                if i in post:
                    del post[i]


    MANDATORY_BILLING_FIELDS = [
        "name",
        "phone",
        "email",
        "street",
        "l10n_br_cnpj_cpf",
        "l10n_br_number",
        "l10n_br_district",
        "zipcode",
        "company_type",
        "city_id",
        "state_id",
        "country_id",
    ]
    OPTIONAL_BILLING_FIELDS = ["street2"]

    @http.route(["/my/account"], type="http", auth="user", website=True)
    def account(self, redirect=None, **post):
        self.update_client(post)
        if "zip" in post:
            post["zipcode"] = post.pop("zip")
        return super(BrWebsiteMyAccount, self).account(
            redirect=redirect, **post
        )
