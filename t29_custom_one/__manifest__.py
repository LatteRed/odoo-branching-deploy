{
    'name': 'T29 CRM Extension',
    'version': '1.0.0',
    'category': 'CRM',
    'summary': 'Simple CRM extensions for T29',
    'description': 'Basic CRM lead extensions with custom fields',
    'author': 'T29 Team',
    'depends': ['base', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
