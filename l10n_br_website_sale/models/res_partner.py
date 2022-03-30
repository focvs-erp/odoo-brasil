# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.http import request
from typing import Dict, List


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _verify_who_is_resposible(self, all_values: Dict, attr_list: List) -> bool:
        return any({x: all_values.get(x, False) for x in attr_list}.values())

    # AX4B - LICENSE HOLDER
    def write_partner_contact(self, partner_id, all_values):
        Partner = request.env["res.partner"].sudo()

        partner_responsible = {
            'name': all_values.get('name_responsible', False),
            'email': all_values.get('email_responsible', False),
            'phone': all_values.get('phone_responsible', False),
        }

        if self._verify_who_is_resposible(all_values, ['name_responsible','email_responsible','phone_responsible']):
            respo_billing = Partner.search([("responsible_billing", "=", True), ('parent_id', '=', partner_id)])
            if respo_billing.exists():
                if all_values.get('checkbox_responsible_license', False):
                    Partner.search([("responsible_billing", "=", False), ("responsible_license", "=", True), ('parent_id', '=', partner_id)]).unlink()
                    partner_responsible.update({'responsible_license': True, 'type': 'responsible'})
                    respo_billing.write(partner_responsible)

                else:
                    partner_responsible.update({'type': 'contact'})
                    respo_billing.write(partner_responsible)
            else:
                partner_responsible.update({
                    'parent_id': partner_id,
                    'type': 'responsible',
                    'website_contact': True,
                    'responsible_billing': True,
                    'responsible_license': True if all_values.get('checkbox_responsible_license', None) or not all_values.get('checkbox_responsible_license', False) and not self._verify_who_is_resposible(all_values, [
                        'name_responsible_for_license', 
                        'email_responsible_for_license', 
                        'phone_responsible_for_license']) else False
                    }
                    )
                Partner.create(partner_responsible)

        if not all_values.get('checkbox_responsible_license', False):
            partner_responsible = {
                'name': all_values.get('name_responsible_for_license', False),
                'email': all_values.get('email_responsible_for_license', False),
                'phone': all_values.get('phone_responsible_for_license', False),
            }
            if self._verify_who_is_resposible(all_values, [
                'name_responsible_for_license', 
                'email_responsible_for_license',
                'phone_responsible_for_license']):

                respo_license = Partner.search([("responsible_license", "=", True), ('parent_id', '=', partner_id)])

                if respo_license.exists() and respo_license[0].responsible_billing == False:
                    respo_license.write(partner_responsible)

                else:
                    if respo_license.exists() and respo_license[0].responsible_billing == True:
                        respo_license.write({'type': 'contact','responsible_license': False})

                    partner_responsible.update({
                        'parent_id': partner_id,
                        'type': 'responsible',
                        'website_contact': True,
                        'responsible_billing': False,
                        'responsible_license': True
                    })
                    Partner.create(partner_responsible)
            else:
                Partner.search([("responsible_license", "=", True), ("responsible_billing", "=", False), ('parent_id', '=', partner_id)]).unlink()

    def address_get(self, adr_pref=None):

        """ Find contacts/addresses of the right type(s) by doing a depth-first-search
        through descendants within company boundaries (stop at entities flagged ``is_company``)
        then continuing the search at the ancestors that are within the same company boundaries.
        Defaults to partners of type ``'default'`` when the exact type is not found, or to the
        provided partner itself if no type ``'default'`` is found either. """
        adr_pref = set(adr_pref or [])
        if 'contact' not in adr_pref:
            adr_pref.add('contact')
        result = {}
        visited = set()
        for partner in self:
            current_partner = partner
            while current_partner:
                to_scan = [current_partner]
                # Scan descendants, DFS
                while to_scan:
                    record = to_scan.pop(0)
                    visited.add(record)
                    if not record.website_contact and record.type in adr_pref and not result.get(record.type):
                        result[record.type] = record.id
                    if len(result) == len(adr_pref):
                        return result
                    to_scan = [c for c in record.child_ids
                                 if c not in visited
                                 if not c.is_company] + to_scan

                # Continue scanning at ancestor if current_partner is not a commercial entity
                if current_partner.is_company or not current_partner.parent_id:
                    break
                current_partner = current_partner.parent_id

        # default to type 'contact' or the partner itself
        default = result.get('contact', self.id or False)
        for adr_type in adr_pref:
            result[adr_type] = result.get(adr_type) or default
        return result