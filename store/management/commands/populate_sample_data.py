from django.core.management.base import BaseCommand
from store.models import Category, Product

class Command(BaseCommand):
    help = 'Populates the database with sample categories and products.'

    def handle(self, *args, **options):
        # Sample categories
        categories = [
            'Perfume',
            'Candles',
            'Diffusers',
            'Essential Oils',
            'Room Sprays',
        ]
        created_categories = []
        for name in categories:
            cat, created = Category.objects.get_or_create(name=name)
            created_categories.append(cat)
        self.stdout.write(self.style.SUCCESS(f'Created {len(created_categories)} categories.'))

        # Sample products
        products = [
            {'name': 'Ocean Breeze', 'category': created_categories[0], 'price': 29.99},
            {'name': 'Vanilla Candle', 'category': created_categories[1], 'price': 19.99},
            {'name': 'Lavender Diffuser', 'category': created_categories[2], 'price': 24.99},
            {'name': 'Peppermint Oil', 'category': created_categories[3], 'price': 14.99},
            {'name': 'Citrus Room Spray', 'category': created_categories[4], 'price': 12.99},
        ]
        created_products = []
        for prod in products:
            p, created = Product.objects.get_or_create(
                name=prod['name'],
                defaults={
                    'category': prod['category'],
                    'price': prod['price'],
                    'description': f'Sample description for {prod["name"]}',
                    'is_active': True,
                }
            )
            created_products.append(p)
        self.stdout.write(self.style.SUCCESS(f'Created {len(created_products)} products.'))
        self.stdout.write(self.style.SUCCESS('Sample data population complete!'))
