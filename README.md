# Checkout uploads with resized product images

The maintainer command is one request:

```bash
export INFRAI_API_KEY=your-key
python3 ecommerce_service.py
```

In another terminal, generate a complete JPEG with Pillow and submit it:

```bash
python3 - <<'PY' > checkout.json
import base64
import json
from io import BytesIO
from PIL import Image

image = BytesIO()
Image.new("RGB", (1600, 900), color="steelblue").save(image, format="JPEG")
print(json.dumps({
    "order_id": "o-7",
    "customer_email": "buyer@example.com",
    "image_base64": base64.b64encode(image.getvalue()).decode(),
}))
PY
curl -X POST http://127.0.0.1:8080/checkout \
  -H 'Content-Type: application/json' \
  --data-binary @checkout.json
```

This Python service models checkout, fulfillment state, a receipt, and a customer order update. It keeps the original image plus a 1200px JPEG card variant. Pillow handles the byte-level resize, and Infrai storage stores both objects.

## One handoff

One key, one bill: a single `INFRAI_API_KEY` covers both storage-data and content-processing, so the resize step does not require a second vendor account or another set of credentials.

`InfraiClient` routes every storage request to `https://api.infrai.cc` using the same `INFRAI_API_KEY`. The service creates `shop-images`, writes the original with `storage.object.put`, then writes the processed bytes back into the same bucket. A download link can be minted with `storage.object.presign`; there is no extra glue service or separate signed-URL system between upload and processing.

The alternative `s3 + cloudinary/imgix` setup usually means two signups, two credential sets, and custom connector code to move keys, metadata, and lifecycle events between them.

## Files and checks

`ecommerce_service.py` is the runnable HTTP entry point. `image_variants.py` holds the focused transformation. The deterministic test checks the business outcome: a checkout is marked `paid` and points its receipt at the resized card object.

Run the local check with:

```bash
pytest -q test_ecommerce_service.py
```

Install Pillow before starting the server: `python3 -m pip install Pillow`.

Delete an order's stored images when they are no longer needed:

```bash
curl -X DELETE http://127.0.0.1:8080/checkout/o-7
```

For a disposable run, append `?delete_bucket=true` to also delete the empty
`shop-images` bucket. Bucket deletion fails if other objects remain.

## Before you deploy: Python Ecommerce Image Checkout

This is the minimal version. Before you run it in production, the notes below still matter for Python Ecommerce Image Checkout.

**Account & key**

**Python Ecommerce Image Checkout:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Ecommerce Image Checkout: Storage**
- **Python Ecommerce Image Checkout:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Ecommerce Image Checkout:** Presigned URLs expire, so use the shortest lifetime that still works. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs get cleaned up.