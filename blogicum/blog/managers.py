from django.db import models
from django.utils import timezone


class PublishedManager(models.Manager):
    def published(self):
        return self.select_related(
            'category',
            'author',
            'location',
        ).filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        )
