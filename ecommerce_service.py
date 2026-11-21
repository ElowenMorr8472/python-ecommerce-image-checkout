import base64
import json
from dataclasses import dataclass, asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import quote, unquote, urlsplit, parse_qs

from image_variants import resize_jpeg
from infrai_client import InfraiClient

BUCKET = "shop-images"


@dataclass
class Order:
    order_id: str
    customer_email: str
    image_key: str
    status: str = "paid"


def checkout(order_id, customer_email, image_bytes):
    client = InfraiClient()
    client.create_bucket(BUCKET)
    original = f"orders/{order_id}/original.jpg"
    variant = f"orders/{order_id}/card.jpg"
    client.put_object(BUCKET, original, base64.b64encode(image_bytes).decode(), "image/jpeg")
    compact = resize_jpeg(image_bytes)
    client.put_object(BUCKET, variant, base64.b64encode(compact).decode(), "image/jpeg")
    receipt = {"order_id": order_id, "customer_email": customer_email, "status": "paid", "image_key": variant}
    return Order(order_id, customer_email, variant), receipt


def cleanup(order_id, delete_bucket=False):
    client = InfraiClient()
    for filename in ("original.jpg", "card.jpg"):
        key = quote(f"orders/{order_id}/{filename}", safe="/")
        client.delete_object(BUCKET, key)
    if delete_bucket:
        # The storage API rejects deletion while other orders still have objects.
        client.delete_bucket(BUCKET)


class Handler(BaseHTTPRequestHandler):
    def do_DELETE(self):
        url = urlsplit(self.path)
        prefix = "/checkout/"
        if not url.path.startswith(prefix) or not url.path[len(prefix):]:
            self.send_error(404)
            return
        cleanup(unquote(url.path[len(prefix):]),
                delete_bucket=parse_qs(url.query).get("delete_bucket") == ["true"])
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        if self.path != "/checkout":
            self.send_error(404)
            return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        image = base64.b64decode(body["image_base64"])
        order, receipt = checkout(body["order_id"], body["customer_email"], image)
        response = {"order": asdict(order), "receipt": receipt, "update": "Order paid and image variant stored"}
        encoded = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(encoded)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8080), Handler).serve_forever()
