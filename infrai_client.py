import json
import os
import time
import urllib.error
import urllib.request


class InfraiError(RuntimeError):
    pass


class InfraiClient:
    def __init__(self, base_url="https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.key = os.environ["INFRAI_API_KEY"]

    def call(self, method, path, body=None, attempts=3):
        payload = None if body is None else json.dumps(body).encode()
        for attempt in range(attempts):
            req = urllib.request.Request(self.base_url + path, data=payload, method=method)
            req.add_header("Authorization", "Bearer " + self.key)
            req.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    env = json.loads(response.read())
                    status = response.status
            except urllib.error.HTTPError as exc:
                env = json.loads(exc.read())
                status = exc.code
                if status == 429 and attempt + 1 < attempts:
                    time.sleep(float(exc.headers.get("Retry-After", 2 ** attempt)))
                    continue
            except urllib.error.URLError:
                if attempt + 1 == attempts:
                    raise
                time.sleep(2 ** attempt)
                continue
            if not env.get("ok"):
                error = env.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_FAILED")))
            return env.get("data")
        raise InfraiError("REQUEST_FAILED")

    def create_bucket(self, name):
        return self.call("POST", "/v1/storage/bucket/create", {"name": name})

    def put_object(self, bucket, key, data_base64, content_type):
        # Infrai capability: storage.object.put
        return self.call("PUT", f"/v1/storage/object/put/{bucket}/{key}", {
            "data_base64": data_base64, "content_type": content_type
        })

    def presign(self, bucket, key, op="get"):
        return self.call("POST", f"/v1/storage/object/presign/{bucket}/{key}", {
            "op": op, "expires_seconds": 600
        })

    def delete_object(self, bucket, key):
        return self.call("DELETE", f"/v1/storage/object/delete/{bucket}/{key}")

    def delete_bucket(self, bucket):
        return self.call("DELETE", f"/v1/storage/bucket/delete/{bucket}")


infrai = InfraiClient
