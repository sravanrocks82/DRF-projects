from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from .serializers import PaymentSerializer
import paypalrestsdk
import logging

logger = logging.getLogger(__name__)

class PaymentCreateView(APIView):
    def post(self, request):
        try:
            serializer = PaymentSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data

            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": "https://payment-gateway-api-2c52.onrender.com/api/v1/payment/execute",
                    "cancel_url": "https://payment-gateway-api-2c52.onrender.com/api/v1/payment/cancel"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": "Business Payment",
                            "sku": "001",
                            "price": str(data['amount']),
                            "currency": "USD",
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(data['amount']),
                        "currency": "USD"
                    },
                    "description": f"Payment by {data['customer_name']}"
                }]
            })

            if payment.create():
                new_payment = Payment.objects.create(
                    customer_name=data['customer_name'],
                    customer_email=data['customer_email'],
                    amount=data['amount'],
                    paypal_payment_id=payment.id,
                    status='created'
                )
                return Response({
                    "status": "success",
                    "payment_id": new_payment.id,
                    "paypal_payment_id": payment.id,
                    "approval_url": next(link.href for link in payment.links if link.rel == "approval_url")
                }, status=status.HTTP_201_CREATED)

            logger.error(f"PayPal payment creation failed: {payment.error}")
            return Response({"status": "error", "message": str(payment.error)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in PaymentCreateView: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentStatusView(APIView):
    def get(self, request, pk):
        try:
            payment = Payment.objects.get(id=pk)
            serializer = PaymentSerializer(payment)
            return Response({
                "payment": serializer.data,
                "status": "success",
                "message": "Payment details retrieved successfully."
            }, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Payment not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in PaymentStatusView for pk={pk}: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "message": "An unexpected error occurred."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentExecuteView(APIView):
    def get(self, request):
        try:
            payment_id = request.GET.get('paymentId')
            payer_id = request.GET.get('PayerID')
            if not payment_id or not payer_id:
                return Response({
                    "status": "error",
                    "message": "Missing paymentId or PayerID. Please ensure the payment is approved via PayPal."
                }, status=status.HTTP_400_BAD_REQUEST)

            payment = paypalrestsdk.Payment.find(payment_id)
            if payment.execute({"payer_id": payer_id}):
                db_payment = Payment.objects.get(paypal_payment_id=payment_id)
                db_payment.status = 'completed'
                db_payment.save()
                return Response({
                    "status": "success",
                    "message": "Payment executed successfully",
                    "payment_id": db_payment.id
                }, status=status.HTTP_200_OK)
            else:
                error = payment.error
                logger.error(f"Payment execution failed: {error}")
                if error.get('name') == 'PAYMENT_NOT_APPROVED_FOR_EXECUTION':
                    return Response({
                        "status": "error",
                        "message": "Payment not approved by payer. Please complete approval on PayPal."
                    }, status=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "status": "error",
                    "message": str(error)
                }, status=status.HTTP_400_BAD_REQUEST)
        except paypalrestsdk.ResourceNotFound:
            return Response({
                "status": "error",
                "message": "Payment not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Payment.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Payment not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in PaymentExecuteView: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentCancelView(APIView):
    def get(self, request):
        try:
            payment_id = request.GET.get('paymentId')
            if not payment_id:
                return Response({
                    "status": "error",
                    "message": "Missing paymentId"
                }, status=status.HTTP_400_BAD_REQUEST)

            db_payment = Payment.objects.get(paypal_payment_id=payment_id)
            db_payment.status = 'cancelled'
            db_payment.save()
            return Response({
                "status": "success",
                "message": "Payment cancelled successfully",
                "payment_id": db_payment.id
            }, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Payment not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in PaymentCancelView: {str(e)}", exc_info=True)
            return Response({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
