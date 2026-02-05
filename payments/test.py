
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
import paypalrestsdk

class PaymentTests(APITestCase):
    def setUp(self):
        # Mock PayPal payment
        self.mock_payment = MagicMock()
        self.mock_payment.id = "PAY-123456"
        self.mock_payment.create = lambda: True
        # Mock links as a list of MagicMock objects with rel and href attributes
        link = MagicMock()
        link.rel = "approval_url"
        link.href = "https://paypal.com/approve"
        self.mock_payment.links = [link]
        self.mock_payment.execute = lambda data: True

    @patch('paypalrestsdk.Payment')
    def test_get_payment_status_success(self, MockPayment):
        MockPayment.return_value = self.mock_payment
        create_url = reverse('initiate-payment')
        data = {
            "customer_name": "John Smith",
            "customer_email": "john@example.com",
            "amount": 30.00
        }
        create_response = self.client.post(create_url, data, format='json')
        payment_id = create_response.data.get("payment_id")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        status_url = reverse('payment-status', args=[payment_id])
        response = self.client.get(status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["payment"]["customer_name"], "John Smith")

    def test_create_payment_missing_fields(self):
        url = reverse('initiate-payment')
        data = {
            "customer_email": "incomplete@example.com"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_payment_invalid_amount(self):
        url = reverse('initiate-payment')
        data = {
            "customer_name": "Test User",
            "customer_email": "test@example.com",
            "amount": "invalid"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('paypalrestsdk.Payment')
    def test_payment_execute_success(self, MockPayment):
        MockPayment.return_value = self.mock_payment
        MockPayment.find.return_value = self.mock_payment
        create_url = reverse('initiate-payment')
        data = {
            "customer_name": "John Smith",
            "customer_email": "john@example.com",
            "amount": 30.00
        }
        create_response = self.client.post(create_url, data, format='json')
        payment_id = create_response.data.get("payment_id")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        execute_url = reverse('payment-execute') + f'?paymentId=PAY-123456&PayerID=123'
        response = self.client.get(execute_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

    @patch('paypalrestsdk.Payment')
    def test_payment_execute_not_found(self, MockPayment):
        # Mock ResourceNotFound with a mock response object
        mock_response = MagicMock()
        mock_response.status_code = 404
        MockPayment.find.side_effect = paypalrestsdk.ResourceNotFound(response=mock_response)
        execute_url = reverse('payment-execute') + f'?paymentId=INVALID&PayerID=123'
        response = self.client.get(execute_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error")

    @patch('paypalrestsdk.Payment')
    def test_payment_cancel_success(self, MockPayment):
        MockPayment.return_value = self.mock_payment
        create_url = reverse('initiate-payment')
        data = {
            "customer_name": "John Smith",
            "customer_email": "john@example.com",
            "amount": 30.00
        }
        create_response = self.client.post(create_url, data, format='json')
        payment_id = create_response.data.get("payment_id")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        cancel_url = reverse('payment-cancel') + f'?paymentId=PAY-123456'
        response = self.client.get(cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")

    def test_payment_cancel_not_found(self):
        cancel_url = reverse('payment-cancel') + f'?paymentId=INVALID'
        response = self.client.get(cancel_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["status"], "error") 
    @patch('paypalrestsdk.Payment')
    def test_payment_execute_missing_payer_id(self, MockPayment):
        mock_payment = MagicMock()
        mock_payment.id = "PAY-123456"
        MockPayment.find.return_value = mock_payment
        execute_url = reverse('payment-execute') + '?paymentId=PAY-123456'
        response = self.client.get(execute_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Missing paymentId or PayerID. Please ensure the payment is approved via PayPal.")
