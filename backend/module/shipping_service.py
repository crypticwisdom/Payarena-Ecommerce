import datetime
import json
import uuid

import requests
from django.conf import settings

from home.utils import log_request

base_url = settings.SHIPPING_BASE_URL
email = settings.SHIPPING_EMAIL
password = settings.SHIPPING_PASSWORD


class ShippingService:
    @classmethod
    def login(cls):
        from home.utils import log_request
        url = f"{base_url}/login"
        payload = json.dumps({"email": email, "password": password})
        response = requests.request("POST", url, data=payload, headers={"Content-Type": "application/json"}).json()
        log_request(f"url: {url}", f"payload: {payload}", f"response: {response}")
        return response["token"]

    @classmethod
    def get_header(cls):
        token = settings.SHIPPING_TOKEN
        # token = cls.login()
        header = dict()
        header["Authorization"] = f"Bearer {token}"
        header["Content-Type"] = "application/json"
        return header

    @classmethod
    def get_states_with_stations(cls, **kwargs):
        header = cls.get_header()
        url = f"{base_url}/operations/stateInfo?StateName={kwargs.get('state_name')}"
        if kwargs.get('city_name'):
            url = f"{base_url}/operations/stateInfo?StateName={kwargs.get('state_name')}&CityName={kwargs.get('city_name')}"

        response = requests.request("GET", url, headers=header, verify=False).json()
        log_request(f"url: {url}", f"headers: {header}", f"response: {response}")
        return response

    @classmethod
    def get_all_states(cls):
        header = cls.get_header()
        url = f"{base_url}/operations/states"
        response = requests.request("GET", url, headers=header, verify=False).json()
        log_request(f"url: {url}", f"headers: {header}", f"response: {response}")
        return response

    @classmethod
    def rating(cls, **kwargs):
        header = cls.get_header()

        pickup_date = datetime.datetime.today().date() + datetime.timedelta(days=2)
        pickup_time = datetime.datetime.now().time()
        seller_prods = kwargs.get("sellers")
        customer = kwargs.get("customer")
        customer_address = kwargs.get("customer_address")

        shipment_information = list()
        payload = dict()

        overall_weight = list()
        payload["ShipmentInformation"] = shipment_information

        for order_prod in seller_prods:
            seller = order_prod["seller"]
            seller_products = order_prod["products"]
            shipment = list()

            merchant = dict()

            merchant["PickupAddress"] = seller.get_full_address()
            merchant["PickupCoordinate"] = dict()
            # merchant["PickupCoordinate"]["Latitude"] = 6.639438
            # merchant["PickupCoordinate"]["Longitude"] = 3.330983
            merchant["PickupCoordinate"]["Latitude"] = seller.latitude
            merchant["PickupCoordinate"]["Longitude"] = seller.longitude
            merchant["PickupTime"] = str(pickup_time)
            merchant["PickupDate"] = str(pickup_date).replace("-", "/")
            merchant["PickupCity"] = seller.city
            merchant["PickupState"] = seller.state
            merchant["PickupStationId"] = 4
            merchant["SenderNumber"] = f"0{seller.phone_number[-10:]}"
            merchant["SenderName"] = seller.user.get_full_name()
            merchant["ReceiverName"] = customer.user.get_full_name()
            merchant["ReceiverPhoneNumber"] = f"0{customer.phone_number[-10:]}"
            merchant["DeliveryAddress"] = customer_address.get_full_address()
            merchant["DeliveryCoordinate"] = dict()
            # merchant["DeliveryCoordinate"]["Latitude"] = 6.5483777
            # merchant["DeliveryCoordinate"]["Longitude"] = 3.3883414
            merchant["DeliveryCoordinate"]["Latitude"] = customer_address.latitude
            merchant["DeliveryCoordinate"]["Longitude"] = customer_address.longitude
            merchant["DeliveryState"] = customer_address.state
            merchant["DeliveryStationId"] = 4
            merchant["DeliveryCity"] = customer_address.city
            merchant["Items"] = shipment
            shipment_information.append(merchant)

            prod_weight = 0
            uid = ""
            total_item_weight = list()

            for product in seller_products:
                item = dict()
                quantity = product.get('quantity')
                uid = product.get('merchant_id')
                weight = product.get("weight")
                price = product.get("price")
                description = product.get("detail")
                amount = (price * quantity)
                prod_weight += (weight * quantity)
                prod = product.get("product")

                item["PackageId"] = prod.id
                item["Quantity"] = quantity
                item["Weight"] = prod_weight
                item["ItemType"] = "Normal"
                item["Name"] = prod.name
                item["Amount"] = float(amount)
                item["ShipmentType"] = "Regular"
                item["Description"] = description
                total_item_weight.append(prod_weight)
                shipment.append(item)

            merchant_order_weight = sum(total_item_weight)
            merchant["Id"] = uid
            merchant["TotalWeight"] = merchant_order_weight
            overall_weight.append(merchant_order_weight)

        payload["TotalWeight"] = sum(overall_weight)
        payload = json.dumps(payload)
        log_request(f"payload ------->>>>> {payload}")

        url = f"{base_url}/operations/quote"

        response = requests.request("POST", url, data=payload, headers=header, verify=False).json()
        log_request(f"url: {url}", f"payload: {payload}", f"response: {response}")
        return response

    @classmethod
    def get_shippers(cls):
        header = cls.get_header()
        url = f"{base_url}/operations/shippers"
        response = requests.request("GET", url, headers=header, verify=False).json()
        log_request(f"url: {url}", f"headers: {header}", f"response: {response}")
        return response

    @classmethod
    def get_all_shippers(cls):
        header = cls.get_header()
        url = f"{base_url}/shippers"
        response = requests.request("GET", url, headers=header, verify=False).json()
        log_request(f"url: {url}", f"headers: {header}", f"response: {response}")
        return response

    @classmethod
    def update_shipper(cls, pk, **kwargs):
        header = cls.get_header()
        url = f"{base_url}/shippers/{pk}/update"
        data = {key: value for key, value in kwargs.items() if value is not None}
        payload = json.dumps(data)
        response = requests.request("POST", url, headers=header, data=payload, verify=False).json()
        log_request(f"url: {url}", f"headers: {header}", f"payload: {payload}", f"response: {response}")
        return response

    @classmethod
    def pickup(cls, **kwargs):
        header = cls.get_header()

        pickup_date = datetime.datetime.today().date()
        pickup_time = datetime.datetime.now().time()

        all_order = kwargs.get("order_products")
        address = kwargs.get("address")

        retry = kwargs.get("retry")

        shipment_information = list()
        shipper_names = list()

        payload = dict()

        for order in all_order:
            shipper_names.append(order.shipper_name)
            shipper_names = [*set(shipper_names)]

        for shipper in shipper_names:
            order_products = all_order.filter(shipper_name=shipper)
            detail = dict()
            order_product = order_products.first()
            order_number = f"PAYMALL-{order_product.order_id}{order_product.id}"
            if retry:
                order_number = f"PAYMALL-{order_product.order_id}{order_product.id}-{str(uuid.uuid4().int)[:3]}"
            seller = order_product.product_detail.product.store.seller
            customer = order_product.order.customer

            detail["ShipperName"] = order_product.shipper_name
            detail["OrderNo"] = order_number
            if str(order_product.company_id).isnumeric():
                detail["CompanyId"] = int(order_product.company_id)
            detail["Summary"] = order_product.product_detail.product.description
            detail["DeliveryRequestedTime"] = "06 AM to 09 PM"
            detail["PickupTime"] = str(pickup_time)
            detail["PickupDate"] = str(pickup_date).replace("-", "/")
            detail["PickupCoordinate"] = dict()
            # detail["PickupCoordinate"]["Latitude"] = 6.639438
            # detail["PickupCoordinate"]["Longitude"] = 3.330983
            detail["PickupCoordinate"]["Latitude"] = seller.latitude
            detail["PickupCoordinate"]["Longitude"] = seller.longitude
            detail["PickUpLandmark"] = seller.town
            detail["PickupAddress"] = seller.get_full_address()
            detail["SenderPhoneNumber"] = f"0{seller.phone_number[-10:]}"
            detail["SenderName"] = seller.user.get_full_name()
            detail["SenderEmail"] = seller.user.email
            detail["RecipientEmail"] = customer.user.email
            detail["DeliveryAddress"] = address.get_full_address()
            detail["DeliveryCoordinate"] = dict()
            # detail["DeliveryCoordinate"]["Latitude"] = 6.5483777
            # detail["DeliveryCoordinate"]["Longitude"] = 3.3883414
            detail["DeliveryCoordinate"]["Latitude"] = address.latitude
            detail["DeliveryCoordinate"]["Longitude"] = address.longitude
            detail["DeliveryType"] = "Normal"
            detail["DeliveryTime"] = "4 AM to 7 PM"
            detail["ReceiverPhoneNumber"] = f"0{customer.phone_number[-10:]}"
            detail["ReceiverName"] = customer.user.get_full_name()
            detail["PickupState"] = seller.state
            detail["DeliveryState"] = address.state
            detail["TotalWeight"] = order_product.product_detail.weight
            detail["PickupStationId"] = 4
            detail["DeliveryStationId"] = 4
            detail["SenderTownId"] = seller.town_id
            detail["ReceiverTownId"] = address.town_id
            detail["PickupCity"] = seller.city
            detail["DeliveryCity"] = address.city

            shipment = list()
            for product in order_products:
                shipment_item = dict()
                shipment_item["PackageId"] = product.id
                shipment_item["IsDelivered"] = 0
                shipment_item["Name"] = product.product_detail.product.name
                shipment_item["Quantity"] = product.quantity
                shipment_item["Color"] = product.product_detail.color
                shipment_item["Size"] = product.product_detail.size
                shipment_item["Description"] = product.product_detail.product.description
                shipment_item["Distance"] = 5
                shipment_item["WeightRange"] = 0
                shipment_item["Weight"] = product.product_detail.weight
                shipment_item["Amount"] = float(product.total)
                shipment_item["ItemType"] = "Normal"
                shipment_item["ShipmentType"] = "Regular"
                shipment_item["PickUpGooglePlaceAddress"] = seller.get_full_address()
                shipment_item["DeliveryContactName"] = customer.user.get_full_name()
                shipment_item["DeliveryContactNumber"] = f"0{customer.phone_number[-10:]}"
                shipment_item["DeliveryGooglePlaceAddress"] = address.get_full_address()
                shipment_item["DeliveryLandmark"] = address.town
                shipment_item["DeliveryState"] = address.state
                shipment_item["DeliveryCity"] = address.city
                shipment_item["PickupState"] = seller.state
                shipment_item["PickupCity"] = seller.city
                shipment.append(shipment_item)

            detail["ShipmentItems"] = shipment
            shipment_information.append(detail)

        payload["ShipmentInformation"] = shipment_information
        payload["Summary"] = kwargs.get("order_summary")

        payload = json.dumps(payload)

        url = f"{base_url}/operations/bookOrders"
        response = requests.request("POST", url, data=payload, headers=header, verify=False).json()
        log_request(f"url: {url}", f"payload: {payload}", f"response: {response}")
        return response

    @classmethod
    def track_order(cls, tracking_id):
        header = cls.get_header()
        url = f"{base_url}/operations/trackShipment?orderNo={tracking_id}"
        response = requests.request("GET", url, headers=header, verify=False).json()
        log_request(f"url: {url}", f"headers: {header}", f"response: {response}")
        return response








