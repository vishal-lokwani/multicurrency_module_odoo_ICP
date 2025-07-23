{
    'name': 'ICP Currency Module', 
    'summary': 'ICP Currency 18 module',
    'description': '''
        Connects ICP transactions with odoo currency module.
    ''',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'license': 'LGPL-3', 
    'author': 'Vidhema Technologies',
    'website': 'https://www.vidhema.com',
    'depends': [
        'base',
    ],
    'price':'100',
    'currency': 'USD',
    'data': [
        'data/currency_cron.xml',
    ],
    'image': ['static/description/icp.gif'],
    'installable': True,
    'application': True,

}
