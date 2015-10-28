# -*- encoding: utf-8 -*-
##############################################################################
#    Copyright (c) 2015 - Present Teckzilla Software Solutions Pvt. Ltd. All Rights Reserved
#    Author: [Teckzilla Software Solutions]  <[sales@teckzilla.net]>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of the GNU General Public License is available at:
#    <http://www.gnu.org/licenses/gpl.html>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp import exceptions as odoo_exceptions

class sale_order(models.Model):
    _inherit = "sale.order"
    
    wcfmc_id = fields.Integer(string="WCFMC ID")
    vehicle_registration = fields.Char(string="Vehicle Registration")
    make_model = fields.Char(string="Make and Model")
    fuel = fields.Selection([('petrol', 'Petrol'),('diesel', 'Diesel')], string='Fuel')
    transmission = fields.Selection([('manual', 'Manual'),('automatic', 'Automatic')], string='Transmission')
    registration_year = fields.Integer(string="Registration Year")
    city = fields.Char(string="City")
    postcode = fields.Char(string="Postcode")

    @api.model
    def create(self, vals):
        so = super(sale_order, self).create(vals)
        so.wcfmc_upload()
        return so

    @api.multi
    def action_wcfmc_upload(self):
        for so in self:
            if so.can_upload():
                so.wcfmc_upload()
            else:
                raise odoo_exceptions.except_orm(_("Missing WCFMC Data"),\
                    _("Only quotations in state draft and with the following fields filled can be uploaded to WhoCanFixMyCar:\n\n"\
                        + "\n - WCFMC ID"\
                        + "\n - Vehicle Registration"\
                        + "\n - Make and Model"\
                        + "\n - Registration Year"\
                        + "\n - City"\
                        + "\n - Postcode"))

    def can_upload(self):
        return (self.wcfmc_id != 0 and self.state == 'draft' and len(self.order_line) > 0\
                and self.name and self.vehicle_registration and self.make_model and self.registration_year\
                and self.city and self.postcode)

    def wcfmc_upload(self):
        """ Send quotation to WCFMC """
        if self.can_upload():
            wcfmc_id = self.wcfmc_id

            # construct message get quote total
            quote = str(self.amount_total)
            message = self.env["ir.config_parameter"].get_param("cm.wcfmc.quote_message")
            if not message:
                raise odoo_exceptions.except_orm(_("Quote Message Missing"),\
                    _("Please set a WCFMC quote message in Settings > General Settings > WCFMC Settings"))
            message = message.replace('{price}', str(self.amount_total))
            message = message.replace('{name}', self.partner_id.name)
            message = message.replace('{wcfmc_id}', str(self.wcfmc_id))
            message = message.replace('{vehicle_registration}', self.vehicle_registration)
            message = message.replace('{make_model}', self.make_model)
            message = message.replace('{registration_year}', str(self.registration_year))
            message = message.replace('{city}', self.city)
            message = message.replace('{postcode}', self.postcode)

            wcfmc = self.env['cm.cron'].get_wcfmc_instance()
            wcfmc.apply_for_job(wcfmc_id, message, quote)
            
            self.state = 'sent'
        
sale_order()
