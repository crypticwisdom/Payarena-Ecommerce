from rest_framework.exceptions import APIException

from home.utils import log_request


class InvalidRequestException(APIException):
    status_code = 400
    default_detail = 'Invalid request'
    default_code = 'invalid_request'


def create_error_message(key, values):
    data = dict()
    data[key] = str(values).split('|')
    raise InvalidRequestException({'detail': values})


def raise_serializer_error_msg(errors: {}):
    data = dict()

    for err_key, err_val in errors.items():
        if type(err_val) is list:
            for err_val_val in err_val:
                if type(err_val_val) is dict:
                    for err_val_val_key, err_val_val_val in err_val_val.items():
                        err_msg = ', '.join(err_val_val_val)
                        msg = f'Error occurred on \'{str(err_val_val_key).replace("_", " ")}\' field: {err_msg}'
                        data['detail'] = msg
                        raise InvalidRequestException(data)
                else:
                    continue
            err_msg = ', '.join(err_val)
            msg = f'Error occurred on \'{str(err_key).replace("_", " ")}\' field: {err_msg}'
            data['detail'] = msg
        else:
            for err_val_key, err_val_val in err_val.items():
                if type(err_val_val) is list:
                    err_msg = ', '.join(err_val_val)
                    msg = f'Error occurred on \'{str(err_val_key).replace("_", " ")}\' field: {err_msg}'
                    data['detail'] = msg
                if type(err_val_val) is dict:
                    for err_val_val_key, err_val_val_val in err_val_val.items():
                        err_msg = ', '.join(err_val_val_val)
                        msg = f'Error occurred on \'{str(err_val_key).replace("_", " ")}\' field: {err_msg}'
                        data['detail'] = msg
        log_request(data)
        raise InvalidRequestException(data)

