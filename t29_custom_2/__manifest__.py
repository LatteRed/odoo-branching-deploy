{
    'name': 'T29 Partner Extension',
    'version': '1.0.0',
    'category': 'Sales',
    'summary': 'Simple partner extensions for T29',
    'description': 'Basic partner extensions with custom fields',
    'author': 'T29 Team',
    'license': 'LGPL-3',
    'depends': ['base', 't29_custom_one'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
