from io import BytesIO


def resize_jpeg(image_bytes, max_side=1200, quality=82):
    from PIL import Image
    with Image.open(BytesIO(image_bytes)) as image:
        image = image.convert("RGB")
        image.thumbnail((max_side, max_side))
        output = BytesIO()
        image.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()
