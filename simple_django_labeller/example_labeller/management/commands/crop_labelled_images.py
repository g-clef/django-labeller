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
    help = 'extract the images that have labelled sections and crop them to max 800px height'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str)

    def handle(self, *args, **options):
        path = options['path']
        os.makedirs(path, exist_ok=True)
        for entry in models.ImageWithLabels.objects.all():
            filename = entry.image.name
            labels = json.loads(entry.labels.labels_json_str)
            if labels:
                im = Image.open(entry.image)
                width, height = im.size
                if height > 800:
                    im = im.crop((0, 0, width, 800),)
                im.save(os.path.join(path, filename), quality=100)
                im.close()
