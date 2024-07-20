from rest_framework import status

from rest_framework.views import APIView
from rest_framework.response import Response

from module.shipping_service import ShippingService


class GetLocation(APIView):
    permission_classes = []

    def get(self, request):

        state_name = request.GET.get("state_name")
        city_name = request.GET.get("city_name")

        if state_name and not city_name:
            data = ShippingService.get_states_with_stations(state_name=state_name)

        elif city_name:
            if not state_name:
                return Response({"detail": "State name is required"}, status=status.HTTP_400_BAD_REQUEST)

            data = ShippingService.get_states_with_stations(state_name=state_name, city_name=city_name)
        else:
            response = ShippingService.get_all_states()
            data = list()
            for item in response:
                result = dict()
                result["state_id"] = item["StateID"]
                result["state_name"] = item["StateName"]
                data.append(result)
        return Response(data)
