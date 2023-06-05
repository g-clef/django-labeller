from django.core.management.base import BaseCommand
from ... import models
from PIL import Image
import json

LOGO_CLASSES = {
    "icon",
    "icon_text"
}

LOGIN_FORM_CLASSES = {
    "login_form",
}

CATEGORIES = [
    {"id": 0, "name": "logo"},
    {"id": 1, "name": "login"}
]

STARTING_ID = 200


class Command(BaseCommand):
    help = 'extract the icon/logo bounding box definitions in coco format'
    #
    # coco format is:
    # {"images": [{"file_name": <path to image>,
    #               "height": <int - height of image>
    #               "width": <int - width of image>
    #               "id": <id of image>},
    #               ...
    #           ],
    #  "annotations": [ {"area": <int, size of box>
    #                    "image_id": <int: id from Images section above>
    #                    "bbox": [<x_min>, <y_min>, <width>, <height>],
    #                    "category_id": <int, id from categories section below>
    #                   "iscrowd": 0 or 1 <whether this annotation covers more than one of the thing},
    #                   ...
    #           ],
    #  "categories": [ {"id": <id for the category>, "name": <str, name of the category>},
    #                   ...
    #           ]
    # }
    #
    #

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **options):
        outpath = options['path']
        images = list()
        annotations = list()
        for entry in models.ImageWithLabels.objects.all():
            image_id = entry.id
            path = entry.image.path
            im = Image.open(entry.image)
            width, height = im.size
            im.close()
            image_json = {"file_name": str(path),
                           "height": height,
                           "width": width,
                           "id": image_id}
            labels = json.loads(entry.labels.labels_json_str)
            image_annotations = list()
            for crop in labels:
                if crop['label_class'] in LOGO_CLASSES:
                    category = 0
                elif crop['label_class'] in LOGIN_FORM_CLASSES:
                    category = 1
                else:
                    continue
                center = crop['centre']
                size = crop['size']
                if size['x'] == 0:
                    continue
                if size['y'] == 0:
                    continue
                left = int(center['x']) - int(size['x']/2)
                if left < 0:
                    left = 0
                top = int(center['y']) - int(size['y']/2)
                if top < 0:
                    top = 0
                crop_width = size['x']
                crop_height = size['y']
                bbox = (left, top, crop_width, crop_height)
                image_annotations.append({"area": crop_width*crop_height,
                                          "image_id": image_id,
                                          "bbox": bbox,
                                          "category_id": category,
                                          "iscrowd": 0}
                                        )
            if image_annotations:
                # only include in the output stuff that has bounding boxes defined.
                images.append(image_json)
                annotations.extend(image_annotations)
        with open(outpath, "w") as outfile:
            final_json = {"images": images,
                          "annotations": annotations,
                          "categories": CATEGORIES}
            json.dump(final_json, outfile)
