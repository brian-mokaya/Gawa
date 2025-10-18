"""
PayHero API service for payment processing
Updated to use PayHero v2 API endpoint
"""
import os
import requests
import json
import base64
import uuid
from datetime import datetime
from decimal import Decimal
from .models import Payment


class PayHeroService:
    """Service for PayHero API operations - v2 API"""
    
    def __init__(self):
        self.api_key = os.getenv('PAYHERO_API_KEY')
        self.api_secret = os.getenv('PAYHERO_API_SECRET')
        self.base_url = os.getenv('PAYHERO_BASE_URL', 'https://backend.payhero.co.ke')
        self.channel_id = os.getenv('PAYHERO_CHANNEL_ID')
        self.callback_url = os.getenv('PAYHERO_CALLBACK_URL', 'https://your-domain.com/api/payhero/webhook/')
        self.provider = os.getenv('PAYHERO_PROVIDER', 'm-pesa')
        self.network_code = os.getenv('PAYHERO_NETWORK_CODE', '63902')  # For MPESA
        
        # Allow initialization without credentials for testing
        # if not self.api_key or not self.api_secret:
        #     raise ValueError("PAYHERO_API_KEY and PAYHERO_API_SECRET must be set")
        # 
        # if not self.channel_id:
        #     raise ValueError("PAYHERO_CHANNEL_ID must be set")

    def _get_auth_header(self):
        """Generate Basic Auth header for PayHero v2 API"""
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def initiate_stk_push(self, phone_number: str, amount: float, payment_id: int, 
                          external_reference: str = None, customer_name: str = None) -> dict:
        """
        Initiate STK push for payment via PayHero v2 API
        
        Args:
            phone_number: Customer phone number (e.g., 0787677676 or +254787677676)
            amount: Amount in KES
            payment_id: Internal payment ID for tracking
            external_reference: Your unique reference (e.g., INV-009)
            customer_name: Customer name for display
        
        Returns:
            dict: Response with success status and transaction details
        """
        try:
            # Format phone number to acceptable format
            phone = self._format_phone_number(phone_number)
            
            # Generate references
            external_ref = external_reference or f"PAY-{payment_id}-{uuid.uuid4().hex[:8].upper()}"
            merchant_request_id = str(uuid.uuid4())
            
            # Check if PayHero is configured
            if not self.api_key or not self.api_secret or not self.channel_id:
                # Return mock response for testing
                return {
                    'success': True,
                    'status': 'QUEUED',
                    'reference': 'TEST_' + uuid.uuid4().hex[:8].upper(),
                    'checkout_request_id': 'test_' + merchant_request_id,
                    'merchant_request_id': merchant_request_id,
                    'external_reference': external_ref,
                    'payhero_response': {'status': 'TEST_MODE'},
                    'payment_id': payment_id,
                    'message': 'Test mode - PayHero not configured'
                }
            
            # Prepare request payload
            payload = {
                "amount": float(amount),
                "phone_number": phone,
                "channel_id": int(self.channel_id),
                "provider": self.provider,
                "external_reference": external_ref,
                "customer_name": customer_name or f"Payment {payment_id}",
                "callback_url": self.callback_url,
                "merchant_request_id": merchant_request_id,
            }
            
            # Add network_code for wallet payments
            if self.provider == "sasapay":
                payload["network_code"] = self.network_code
            
            headers = {
                'Authorization': self._get_auth_header(),
                'Content-Type': 'application/json',
            }
            
            # Make request to PayHero v2 API
            response = requests.post(
                f'{self.base_url}/api/v2/payments',
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    'success': True,
                    'status': data.get('status', 'QUEUED'),
                    'reference': data.get('reference'),
                    'checkout_request_id': data.get('CheckoutRequestID'),
                    'merchant_request_id': merchant_request_id,
                    'external_reference': external_ref,
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

    def _format_phone_number(self, phone: str) -> str:
        """
        Format phone number to PayHero acceptable format
        
        Accepts: 0787677676, 254787677676, +254787677676
        Returns: 0787677676
        """
        # Remove any spaces and special characters
        phone = ''.join(filter(lambda x: x.isdigit() or x == '+', phone))
        
        # If starts with +254, convert to 0...
        if phone.startswith('+254'):
            phone = '0' + phone[4:]
        # If starts with 254, convert to 0...
        elif phone.startswith('254'):
            phone = '0' + phone[3:]
        
        # Ensure it starts with 0 and is valid length
        if not phone.startswith('0') or len(phone) != 10:
            raise ValueError(f"Invalid phone number format: {phone}")
        
        return phone

    def check_transaction_status(self, checkout_request_id: str) -> dict:
        """
        Check transaction status using checkout request ID
        
        Note: PayHero v2 API uses callbacks for status updates.
        This is a helper if you need to query status manually.
        """
        try:
            headers = {
                'Authorization': self._get_auth_header(),
                'Content-Type': 'application/json',
            }
            
            # PayHero v2 API status endpoint
            response = requests.get(
                f'{self.base_url}/api/v2/payments/{checkout_request_id}',
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
                    'receipt_number': data.get('MpesaReceiptNumber'),
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

    def process_webhook(self, data: dict) -> dict:
        """
        Process PayHero webhook callback
        
        Webhook payload structure:
        {
            "forward_url": "",
            "response": {
                "Amount": 10,
                "CheckoutRequestID": "ws_CO_...",
                "ExternalReference": "INV-009",
                "MerchantRequestID": "...",
                "MpesaReceiptNumber": "SAE3YULR0Y",
                "Phone": "+254709099876",
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "Status": "Success"
            },
            "status": true
        }
        """
        try:
            # Extract response from webhook
            response_data = data.get('response', data)
            
            result_code = str(response_data.get('ResultCode', 1))
            checkout_request_id = response_data.get('CheckoutRequestID')
            external_reference = response_data.get('ExternalReference')
            receipt_number = response_data.get('MpesaReceiptNumber')
            
            # Find the payment
            payment = Payment.objects.filter(
                payhero_transaction_id=checkout_request_id
            ).first()
            
            if not payment:
                return {
                    'success': False,
                    'message': 'Payment not found',
                    'checkout_request_id': checkout_request_id,
                }
            
            if result_code == '0':
                # Success - ResultCode 0 means success
                payment.status = 'success'
                payment.completed_at = datetime.now()
                payment.transaction_id = receipt_number
                payment.save()
                
                # Update payer's payment history and credit score
                payment.payer.total_payments += payment.amount
                payment.payer.on_time_payments += 1
                payment.payer.update_credit_score()
                
                return {
                    'success': True,
                    'message': 'Payment processed successfully',
                    'payment_id': payment.id,
                    'status': 'success',
                    'receipt_number': receipt_number,
                }
            else:
                # Failed
                payment.status = 'failed'
                payment.save()
                
                # Decrease credit score on failed payment
                payment.payer.total_late_payments += 1
                payment.payer.update_credit_score()
                
                return {
                    'success': False,
                    'message': f'Payment failed: {response_data.get("ResultDesc", "Unknown error")}',
                    'payment_id': payment.id,
                    'result_code': result_code,
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
            }

    def refund_transaction(self, transaction_id: str, amount: float) -> dict:
        """
        Refund a transaction
        
        Note: Implement if PayHero v2 API supports refunds
        """
        try:
            payload = {
                'transaction_id': transaction_id,
                'amount': float(amount),
            }
            
            headers = {
                'Authorization': self._get_auth_header(),
                'Content-Type': 'application/json',
            }
            
            response = requests.post(
                f'{self.base_url}/api/v2/refunds',
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
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


# Singleton instance
_payhero_service = None


def get_payhero_service() -> PayHeroService:
    """Get PayHero service singleton"""
    global _payhero_service
    if _payhero_service is None:
        _payhero_service = PayHeroService()
    return _payhero_service
