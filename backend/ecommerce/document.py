from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from .models import Product


@registry.register_document
class ProductDocument(Document):
    # foreignKeys and M2M
    store = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'is_active': fields.BooleanField(),
        'on_sale': fields.BooleanField()
    })

    category = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField()
    })

    sub_category = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField()
    })

    product_type = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField()
    })

    brand = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField()
    })

    class Index:
        name = 'products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Product
        fields = [
            'name',
            'description',
            'tags',
            'is_featured',
        ]


