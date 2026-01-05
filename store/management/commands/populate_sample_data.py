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

        # Add 20 products for each category
        created_products = []
        for idx, category in enumerate(created_categories):
            for i in range(1, 21):
                product_name = f"{category.name} Product {i}"
                price = round(10 + idx * 5 + i * 1.25, 2)  # Just for variety
                p, created = Product.objects.get_or_create(
                    name=product_name,
                    defaults={
                        'category': category,
                        'price': price,
                        'short_description': f'Sample description for {product_name}',
                        'full_description': f'Sample description for {product_name}',
                        'is_available': True,
                        'size_ml': 50,
                        'concentration': 'edp',
                        'gender': 'unisex',
                    }
                )
                created_products.append(p)
        self.stdout.write(self.style.SUCCESS(f'Created {len(created_products)} products.'))
        self.stdout.write(self.style.SUCCESS('Sample data population complete!'))
