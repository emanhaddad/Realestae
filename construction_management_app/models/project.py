# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    is_construction = fields.Boolean(string='Construction Project?', default=False)

    date_start = fields.Date(string='Start Date', store=True)
    date_end = fields.Date(string='End Date', store=True)
    
    type_of_construction = fields.Selection(
        [('agricultural','Agricultural'),
        ('residential','Residential'),
        ('commercial','Commercial'),
        ('institutional','Institutional'),
        ('industrial','Industrial'),
        ('heavy_civil','Heavy civil'),
        ('environmental','Environmental'),
        ('other','other')],
        string='Types of Construction'
    )
    location_id = fields.Many2one(
        'realestate.city',
        'Location Address'
    )
    maps_url = fields.Char(string='Maps URL',
                           help='URL to Google Maps location (or other providers).')
    notes_ids = fields.One2many(
        'note.note', 
        'project_id', 
        string='Notes',
    )
    notes_count = fields.Integer(
        compute='_compute_notes_count', 
        string="Notes",
        store=True,
    )
    
    @api.depends('notes_ids')
    def _compute_notes_count(self):
        for project in self:
            project.notes_count = len(project.notes_ids)

    # @api.multi #odoo13
    def view_notes(self):
        for rec in self:
            res = self.env.ref('construction_management_app.action_project_note_note')
            res = res.read()[0]
            res['domain'] = str([('project_id','in',rec.ids)])
        return res
