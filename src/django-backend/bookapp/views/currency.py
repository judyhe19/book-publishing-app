from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from ..utils.currency_converter import CurrencyConverter, CurrencyConversionError

class ConvertCurrencyView(APIView):
    """
    Simple endpoint to convert a given amount and currency to USD.
    Used for real-time preview in the frontend.
    """
    def get(self, request):
        amount = request.query_params.get("amount")
        currency = request.query_params.get("currency")

        if not amount or not currency:
            return Response(
                {"error": "Both 'amount' and 'currency' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        currency = currency.strip().upper()

        if currency == "USD":
            return Response({"usd_amount": amount})

        converter = CurrencyConverter()
        try:
            # We don't convert to Decimal here because to_usd handles it
            usd_amount = converter.to_usd(amount, currency)
            return Response({"usd_amount": str(usd_amount)})
        except CurrencyConversionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
