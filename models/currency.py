from odoo import models, api
import requests
import logging
from datetime import datetime, timedelta, timezone
import time

_logger = logging.getLogger(__name__)

class CurrencyRateUpdater(models.Model):
    _inherit = 'res.currency'

    @api.model
    def update_icp_currency_rate(self):
        default_currency = self.env.user.company_id.currency_id
        currency_code = default_currency.name.lower()
        config = self.env['ir.config_parameter'].sudo()

        # Check and create ICP currency if not exists
        icp_currency = self.env['res.currency'].search([('name', '=', 'ICP')], limit=1)
        if not icp_currency:
            _logger.info("Creating ICP currency.")
            icp_currency = self.env['res.currency'].create({
                'name': 'ICP',
                'full_name': 'Internet Computer',
                'symbol': 'ICP',
                'currency_unit_label': 'ICP',
                'rounding': 0.01,
                'decimal_places': 2,
                'position': 'after',
                'active': True
            })

        # Check if historical data has already been fetched
        historical_flag = config.get_param('icp_currency.historical_loaded')

        # Also check if any rates exist for this currency
        has_rates = self.env['res.currency.rate'].search_count([
            ('currency_id', '=', icp_currency.id),
            ('company_id', '=', self.env.company.id)
        ]) > 0

        if not historical_flag or not has_rates:
            _logger.info("Loading ICP historical rates...")
            start_date = datetime(2024, 9, 1)
            end_date = datetime.today() - timedelta(days=1)
            from_timestamp = int(time.mktime(start_date.timetuple()))
            to_timestamp = int(time.mktime(end_date.timetuple()))

            api_url = "https://api.coingecko.com/api/v3/coins/internet-computer/market_chart/range"
            params = {
                'vs_currency': currency_code,
                'from': from_timestamp,
                'to': to_timestamp
            }

            try:
                response = requests.get(api_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                _logger.error(f"Failed to fetch historical data: {e}")
                return "Failed to fetch historical data."

            prices = data.get("prices", [])
            for timestamp, price in prices:
                dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).date()

                existing_rate = self.env['res.currency.rate'].search([
                    ('currency_id', '=', icp_currency.id),
                    ('name', '=', dt),
                    ('company_id', '=', self.env.company.id)
                ], limit=1)

                if existing_rate:
                    _logger.info(f"Rate for ICP on {dt} already exists. Skipping.")
                    continue

                self.env['res.currency.rate'].create({
                    'currency_id': icp_currency.id,
                    'rate': 1 / price,
                    'name': dt,
                    'company_id': self.env.company.id
                })

            _logger.info("Historical ICP data loading complete.")
            config.set_param('icp_currency.historical_loaded', '1')

        # Add or update today's ICP rate
        today = datetime.today().date()
        current_api = f"https://api.coingecko.com/api/v3/simple/price?ids=internet-computer&vs_currencies={currency_code}"

        try:
            response = requests.get(current_api, timeout=10)
            response.raise_for_status()
            data = response.json()
            icp_price = data.get("internet-computer", {}).get(currency_code)
        except Exception as e:
            _logger.error(f"Failed to fetch today's price: {e}")
            return "Today's ICP rate update failed."

        if icp_price:
            existing_rate = self.env['res.currency.rate'].search([
                ('currency_id', '=', icp_currency.id),
                ('name', '=', today),
                ('company_id', '=', self.env.company.id)
            ], limit=1)

            if existing_rate:
                existing_rate.rate = 1 / icp_price
                _logger.info(f"Updated today's ICP rate: {icp_price}")
            else:
                self.env['res.currency.rate'].create({
                    'currency_id': icp_currency.id,
                    'rate': 1 / icp_price,
                    'name': today,
                    'company_id': self.env.company.id
                })
                _logger.info(f"Inserted today's ICP rate: {icp_price}")
        else:
            _logger.warning("ICP price not found in today's data.")

        return "ICP historical (if needed) and current rates inserted."
