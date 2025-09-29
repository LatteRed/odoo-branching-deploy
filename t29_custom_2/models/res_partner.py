# -*- coding: utf-8 -*-

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    t29_category = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
        ('both', 'Both')
    ], string='T29 Category', default='customer')
    
    t29_rating = fields.Integer(string='T29 Rating', default=5)
