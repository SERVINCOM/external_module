{
    'name': 'Sale Configurator Existing Variants',
    'summary': 'Show existing variant choices in the sales configurator',
    'version': '18.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'SERVINCOM SOLUCIONES, S.L.',
    'website': 'https://www.servincom.com',
    'category': 'Sales/Sales',
    'depends': ['sale'],
    'data': [],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'servincom_sale_configurator_existing_variants/static/src/js/combinations.js',
            'servincom_sale_configurator_existing_variants/static/src/js/configurator.js',
            'servincom_sale_configurator_existing_variants/static/src/xml/attribute_values.xml',
        ],
    },
    'installable': True,
    'application': False,
}
