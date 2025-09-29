# -*- coding: utf-8 -*-

from odoo import models, fields


class T29Integration(models.Model):
    _name = 't29.integration'
    _description = 'T29 Integration'

    name = fields.Char(string='Name', required=True)
