import re
from odoo import http, tools, _
from odoo.http import request
from werkzeug.exceptions import Forbidden
import odoo.addons.website_sale.controllers.main as main
from odoo.addons.portal.controllers.portal import CustomerPortal

class BrWebsiteMyAccount(CustomerPortal):
    def remove_post(self, post):
        fields = ['name_responsible', 'email_responsible', 'phone_responsible', 'checkbox_responsible_license', 'name_responsible_for_license', 'email_responsible_for_license', 'phone_responsible_for_license']
        for i in fields:
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
        if "zip" in post:
            self.remove_post(post)
            post["zipcode"] = post.pop("zip")
        return super(BrWebsiteMyAccount, self).account(
            redirect=redirect, **post
        )
