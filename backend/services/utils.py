import requests
from django.conf import settings
import os, shutil
from PIL import Image

PAYARENA_IMAGE_PROCESSOR_CLIENT_TOKEN = settings.IMAGE_PROCESSOR_CLIENT_TOKEN
IMAGE_PROCESSOR_BLOCK_TOKEN = settings.IMAGE_PROCESSOR_CLIENT_TOKEN
def image_processor(block_token_num, image=None):
    try:
        if not block_token_num:
            return False, "'block_token_num' are required arguments"

        # This is a collection of all block tokens of all available names.
        # Each Token is used to identify a particular Validation Block.

        collections_of_block_names = {
            1: settings.IMAGE_PROCESSOR_MERCHANT_STORE_BANNER_TOKEN,
            2: settings.IMAGE_PROCESSOR_MALL_PRODUCT_TOKEN,
            3: settings.IMAGE_PROCESSOR_MALL_HEADER_BANNER_TOKEN,
            4: settings.IMAGE_PROCESSOR_MALL_FOOTER_BANNER_TOKEN,
            5: settings.IMAGE_PROCESSOR_MALL_BIG_BANNER_TOKEN,
            6: settings.IMAGE_PROCESSOR_MALL_MEDIUM_BANNER_TOKEN,
            7: settings.IMAGE_PROCESSOR_MALL_SMALL_BANNER_BLOCK_TOKEN,
            8: settings.IMAGE_PROCESSOR_MALL_MERCHANT_BANNER_BLOCK_TOKEN,
            9: settings.IMAGE_PROCESSOR_MALL_SPA_BRAND_UPLOAD_BLOCK_TOKEN
        }

        IMAGE_BASE_URL: str = settings.IMAGE_PROCESS_BASE_URL
        # HEADER = {'Content-Type': 'multipart/form-data; boundary=<calculated when request is sent>'}
        HEADER = {}
        if image is not None:
            image_item = Image.open(image)
            path_ = rf"{os.getcwd()}/images"

            try:
                if not os.path.exists(path_):
                    os.mkdir(f"{path_}")

                # System only saves with JPEG type not JPG, so I did an Adjust to change all JPGs to JPEG.
                ext = "JPEG" if str(image.name).split(".")[-1].upper() == "JPG" else str(image.name).split(".")[-1].upper()

                # Save image to images / folder.
                image_item.save(fp=f"{path_}/{image.name}", format=ext)
                # shutil.rmtree(path_)
            except (FileNotFoundError, FileExistsError, Exception) as err:
                # Log Error Message
                shutil.rmtree(path_)

            payload = {
                'block_token': collections_of_block_names[block_token_num],
                'client_token': PAYARENA_IMAGE_PROCESSOR_CLIENT_TOKEN
            }
            files = [
                ('images', (f'{image.name}', open(rf'{path_}/{image.name}', 'rb'), f'{image.content_type}'))
            ]
            response = requests.post(url=f"{IMAGE_BASE_URL}/processor/validation", files=files, data=payload, headers=HEADER)

            if response.status_code != 200:
                return False, f"{response.json()['detail']}"

            return True, response.json()['detail']

    except (Exception, ) as err:
        return False, f"{err}"
