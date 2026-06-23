# management/commands/populate_books.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import random

from dealio.apps.accounts.models import CustomUser, Role, Access
from dealio.apps.accounts.models import (
    Author, Publisher, Category, Book, BookAuthor,
    BookDetail, Review, Order, OrderItem, Inventory, InventoryLog
)


class Command(BaseCommand):
    help = 'Populate database with sample book data'

    @transaction.atomic
    def handle(self, *args, **options):
        from django.db.models import Count, Avg, Sum
        from django.contrib.postgres.aggregates import StringAgg

        books = (
            Book.objects
            .select_related("publisher")
            .filter(inventory_records__quantity__gt=0)
            .annotate(
                review_count=Count("reviews"),
                avg_rating=Avg("reviews__rating"),
                categories_str=StringAgg("categories__name", delimiter=", ", distinct=True)
            )
            .filter(review_count__gt=5)
            .order_by("-avg_rating")
            .values(
                "isbn",
                "publisher__name",
                "categories_str",
                "review_count",
                "avg_rating"
            )
        )
        print(books.query)
