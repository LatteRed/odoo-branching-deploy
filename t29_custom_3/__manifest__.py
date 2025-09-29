{
    'name': 'T29 Integration',
    'version': '1.0.0',
    'category': 'Tools',
    'summary': 'Simple integration module for T29',
    'description': 'Basic integration functionality',
    'author': 'T29 Team',
    'license': 'LGPL-3',
    'depends': ['base', 't29_custom_one', 't29_custom_2'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_integration_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
