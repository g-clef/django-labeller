from django.core.management.base import BaseCommand
from ... import models
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import json
import os

LOGO_CLASSES = {
    "icon",
    "icon_text"
}

STARTING_ID = 200

#
# This is a supremely nasty hack.
# The problem: Pillow doesn't completely close filehandles on images somewhere in the open/crop depths.
# I tried context managers, copying the image, explicit closes, nothign worked...I'd get "too many open files"
# halfway through the export. So, this way I just toss the file open into a thread, and let that thread handle
# the problem.
#


def cropper(image_path, output_path, labels):
    im = Image.open(f"/Users/ageeclough/IdeaProjects/g-clef-django-labeller/simple_django_labeller/media/{image_path}")
    file_name = image_path.split("/")[-1]
    domain_name = file_name.rsplit(".", 1)[0]
    image_counter = 0
    width, height = im.size
    for crop in labels:
        if crop['label_class'] not in LOGO_CLASSES:
            continue
        center = crop['centre']
        size = crop['size']
        if size['x'] == 0:
            continue
        if size['y'] == 0:
            continue
        left = int(center['x']) - int(size['x'] / 2)
        if left < 0:
            left = 0
        top = int(center['y']) - int(size['y'] / 2)
        if top < 0:
            top = 0
        right = int(center['x']) + int(size['x'] / 2)
        if right > width:
            right = width
        bottom = int(center['y']) + int(size['y'] / 2)
        if bottom > height:
            bottom = height
        bbox = (left, top, right, bottom)
        print(f"cropping {file_name} to {bbox}")
        with im.crop(bbox) as cropped_im:
            fixed_crop = cropped_im.copy()

        if not os.path.exists(f"{output_path}/{domain_name}/"):
            os.makedirs(f"{output_path}/{domain_name}/", exist_ok=True)
        image_path = f"{output_path}/{domain_name}/{STARTING_ID + image_counter}.png"
        fixed_crop.save(image_path)
        fixed_crop.close()
        image_counter += 1
    im.close()


class Command(BaseCommand):
    help = 'extract the images from the boxes drawn on images to a given directory'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **options):
        path = options['path']
        futures = list()
        with ThreadPoolExecutor(max_workers=2) as executor:
            for entry in models.ImageWithLabels.objects.all():
                file_name = entry.image.name
                labels = json.loads(entry.labels.labels_json_str)
                future = executor.submit(cropper, file_name, path, labels)
                futures.append(future)
            for future in futures:
                future.result()
