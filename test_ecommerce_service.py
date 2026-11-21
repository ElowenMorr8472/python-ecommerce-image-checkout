import base64
from unittest.mock import patch

from ecommerce_service import checkout, cleanup


class FakeClient:
    def create_bucket(self, name):
        return {"name": name}

    def put_object(self, bucket, key, data_base64, content_type):
        return {"key": key}


@patch("ecommerce_service.InfraiClient", FakeClient)
@patch("ecommerce_service.resize_jpeg", lambda data: data[:2])
def test_checkout_records_paid_variant():
    order, receipt = checkout("o-7", "buyer@example.com", b"jpeg")
    assert order.status == "paid"
    assert order.image_key == "orders/o-7/card.jpg"
    assert receipt["image_key"] == order.image_key


def test_cleanup_deletes_objects_before_optional_bucket():
    with patch("ecommerce_service.InfraiClient") as factory:
        cleanup("o-7", delete_bucket=True)
        from unittest.mock import call
        assert factory.return_value.method_calls == [
            call.delete_object("shop-images", "orders/o-7/original.jpg"),
            call.delete_object("shop-images", "orders/o-7/card.jpg"),
            call.delete_bucket("shop-images"),
        ]


def test_cleanup_keeps_shared_bucket_by_default():
    with patch("ecommerce_service.InfraiClient") as factory:
        cleanup("o-7")
        factory.return_value.delete_bucket.assert_not_called()
