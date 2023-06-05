from django.core.management.base import BaseCommand
from ... import models
from PIL import Image
import json
import os

LOGO_CLASSES = {
    "icon",
    "icon_text"
}

STARTING_ID = 200


class Command(BaseCommand):
    help = 'extract the images from the boxes drawn on images to a given directory'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)
        parser.add_argument("csv", type=str)

    def handle(self, *args, **options):
        path = options['path']
        csv_path = options['csv']
        counter = 0
        with open(csv_path, "w") as outfile:
            for entry in models.ImageWithLabels.objects.all():
                domain_name = entry.image.name.rsplit(".", 1)[0]
                im = Image.open(entry.image)
                width, height = im.size
                labels = json.loads(entry.labels.labels_json_str)
                found_crop = False
                for crop in labels:
                    found_crop = True
                    if crop['label_class'] not in LOGO_CLASSES:
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
                    right = int(center['x']) + int(size['x']/2)
                    if right > width:
                        right = width
                    bottom = int(center['y']) + int(size['y']/2)
                    if bottom > height:
                        bottom = height
                    bbox = (left, top, right, bottom)
                    print(f"cropping {entry.image.name} to {bbox}")
                    cropped_im = im.crop(bbox)
                    if not os.path.exists(f"{path}/{domain_name}/"):
                        os.makedirs(f"{path}/{domain_name}/", exist_ok=True)
                    image_path = f"{path}/{domain_name}/{STARTING_ID + counter}.png"
                    cropped_im.save(image_path)
                    counter += 1
                im.close()
                if found_crop:
                    outfile.write(f"{domain_name}\n")
