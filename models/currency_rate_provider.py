from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class CurrencyRateProvider(models.Model):
    _name = "custom.currency"
    _description = "Currency Rate Provider"

    currency_id = fields.Many2one('res.currency', string='Currency')
    amount = fields.Monetary(string='Amount')
    
    @api.model
    def get_currency_data(self):
        # Fetch all currencies from res.currency
        currencies = self.env['res.currency'].search([])

        for currency in currencies:
            _logger.info(f"Currency: {currency.name}, Symbol: {currency.symbol}, Rate: {currency.rate}")
