"""
PayHero API service for payment processing
"""
import os
import requests
import json
import uuid
from datetime import datetime
from decimal import Decimal
from .models import Payment


class PayHeroService:
    """Service for PayHero API operations"""
    
    def __init__(self):
        self.api_key = os.getenv('PAYHERO_API_KEY')
        self.base_url = os.getenv('PAYHERO_BASE_URL', 'https://api.payhero.co.ke')
        self.merchant_email = os.getenv('PAYHERO_MERCHANT_EMAIL', 'merchant@gawa.app')
        self.merchant_code = os.getenv('PAYHERO_MERCHANT_CODE', 'GAWA')
        
        if not self.api_key:
            raise ValueError("PAYHERO_API_KEY must be set")

    def initiate_stk_push(self, phone_number: str, amount: float, payment_id: int) -> dict:
        """Initiate STK push for payment"""
        try:
            # Remove leading +254 and replace with 254
            phone = phone_number.replace('+', '').replace(' ', '')
            if phone.startswith('0'):
                phone = '254' + phone[1:]
            
            merchant_request_id = str(uuid.uuid4())
            checkout_request_id = str(uuid.uuid4())
            
            payload = {
                'amount': float(amount),
                'phone_number': phone,
                'merchant_request_id': merchant_request_id,
                'checkout_request_id': checkout_request_id,
                'merchant_email': self.merchant_email,
                'merchant_code': self.merchant_code,
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            
            response = requests.post(
                f'{self.base_url}/api/v1/stk/push',
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'merchant_request_id': merchant_request_id,
                    'checkout_request_id': checkout_request_id,
                    'payhero_response': data,
                    'payment_id': payment_id,
                }
            else:
                return {
                    'success': False,
                    'message': f'PayHero API error: {response.status_code}',
                    'response': response.text,
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
            }

    def check_transaction_status(self, merchant_request_id: str) -> dict:
        """Check transaction status"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            
            response = requests.get(
                f'{self.base_url}/api/v1/transactions/{merchant_request_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'status': data.get('status'),
                    'amount': data.get('amount'),
                    'phone_number': data.get('phone_number'),
                    'transaction_id': data.get('transaction_id'),
                    'payhero_response': data,
                }
            else:
                return {
                    'success': False,
                    'message': f'PayHero API error: {response.status_code}',
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
            }

    def refund_transaction(self, transaction_id: str, amount: float) -> dict:
        """Refund a transaction"""
        try:
            payload = {
                'transaction_id': transaction_id,
                'amount': float(amount),
                'merchant_email': self.merchant_email,
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            
            response = requests.post(
                f'{self.base_url}/api/v1/refund',
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'payhero_response': response.json(),
                }
            else:
                return {
                    'success': False,
                    'message': f'PayHero API error: {response.status_code}',
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
            }

    def process_webhook(self, data: dict) -> dict:
        """Process PayHero webhook"""
        try:
            result_code = data.get('ResultCode')
            checkout_request_id = data.get('CheckoutRequestID')
            
            # Find the payment
            payment = Payment.objects.filter(
                payhero_transaction_id=checkout_request_id
            ).first()
            
            if not payment:
                return {
                    'success': False,
                    'message': 'Payment not found',
                }
            
            if result_code == '0':
                # Success
                payment.status = 'success'
                payment.completed_at = datetime.now()
                payment.transaction_id = data.get('MpesaReceiptNumber')
                payment.save()
                
                # Update payment history
                payment.payer.total_payments += payment.amount
                payment.payer.on_time_payments += 1
                payment.payer.update_credit_score()
                
                return {
                    'success': True,
                    'message': 'Payment processed',
                    'payment_id': payment.id,
                }
            else:
                # Failed
                payment.status = 'failed'
                payment.save()
                
                return {
                    'success': False,
                    'message': f'Payment failed: {data.get("ResultDesc")}',
                    'payment_id': payment.id,
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
            }


# Singleton instance
_payhero_service = None


def get_payhero_service() -> PayHeroService:
    """Get PayHero service singleton"""
    global _payhero_service
    if _payhero_service is None:
        _payhero_service = PayHeroService()
    return _payhero_service
