from django.core.management.base import BaseCommand
from store.models import Category, Product, Brand, ProductImage
from django.core.files.base import ContentFile
import urllib.request

class Command(BaseCommand):
    help = 'Load demo categories and products with images.'

    def handle(self, *args, **options):
        # 1. Add Categories
        categories = [
            {"name": "Perfume Oils", "description": "Premium concentrated perfume oils.", "is_active": True},
            {"name": "Eau de Parfum (EDP)", "description": "Long-lasting Eau de Parfum fragrances.", "is_active": True},
            {"name": "Body Sprays", "description": "Refreshing body sprays for daily use.", "is_active": True},
            {"name": "Mini Sets", "description": "Miniature perfume sets, perfect for gifts.", "is_active": True},
            {"name": "Gift Sets", "description": "Curated gift sets for special occasions.", "is_active": True},
            {"name": "Testers", "description": "Testers for sampling new scents.", "is_active": True},
        ]
        for cat in categories:
            obj, created = Category.objects.get_or_create(name=cat["name"], defaults=cat)
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Exists'} category: {obj.name}"))

        # 2. Add a Brand (required for Product FK)
        brand, _ = Brand.objects.get_or_create(name="SceaniCollections", defaults={"description": "House brand for demo products."})

        # 3. Add Products with Images
        categories_dict = {c.name: c for c in Category.objects.all()}
        products = [
            {
                "name": "Midnight Rose",
                "category": categories_dict.get("Perfume Oils"),
                "concentration": "oil",
                "size_ml": 50,
                "description": "A captivating blend of rose and bergamot with a sensual base of sandalwood and musk.",
                "price": 15000.00,
                "stock_quantity": 100,
                "top_notes": "Rose, Bergamot",
                "heart_notes": "Jasmine, Lily",
                "base_notes": "Sandalwood, Musk",
                "is_featured": True,
                "is_bestseller": True,
                "is_active": True,
                "images": [
                    "https://images.unsplash.com/photo-1541643600914-78b084683601?w=800",
                    "https://images.unsplash.com/photo-1590736969956-6d9c2a8d6972?w=800"
                ]
            },
            {
                "name": "Citrus Splash",
                "category": categories_dict.get("Body Sprays"),
                "concentration": "edp",
                "size_ml": 100,
                "description": "A fresh burst of citrus and florals for all-day energy.",
                "price": 8000.00,
                "stock_quantity": 80,
                "top_notes": "Lemon, Orange",
                "heart_notes": "Neroli, Jasmine",
                "base_notes": "Cedarwood, Musk",
                "is_featured": True,
                "is_bestseller": False,
                "is_active": True,
                "images": [
                    "https://images.unsplash.com/photo-1590736969956-6d9c2a8d6972?w=800"
                ]
            },
            {
                "name": "Amber Oud",
                "category": categories_dict.get("Eau de Parfum (EDP)"),
                "concentration": "edp",
                "size_ml": 100,
                "description": "Rich amber and oud notes for a luxurious experience.",
                "price": 25000.00,
                "stock_quantity": 50,
                "top_notes": "Amber, Saffron",
                "heart_notes": "Oud, Rose",
                "base_notes": "Patchouli, Vanilla",
                "is_featured": True,
                "is_bestseller": True,
                "is_active": True,
                "images": [
                    "https://images.unsplash.com/photo-1541643600914-78b084683601?w=800"
                ]
            },
            {
                "name": "Mini Discovery Set",
                "category": categories_dict.get("Mini Sets"),
                "concentration": "oil",
                "size_ml": 10,
                "description": "A set of mini perfume oils to discover your favorite scent.",
                "price": 12000.00,
                "stock_quantity": 30,
                "top_notes": "Mixed",
                "heart_notes": "Mixed",
                "base_notes": "Mixed",
                "is_featured": False,
                "is_bestseller": False,
                "is_active": True,
                "images": [
                    "https://images.unsplash.com/photo-1590736969956-6d9c2a8d6972?w=800"
                ]
            },
            {
                "name": "Gift Set Deluxe",
                "category": categories_dict.get("Gift Sets"),
                "concentration": "edp",
                "size_ml": 100,
                "description": "A deluxe gift set for special occasions.",
                "price": 50000.00,
                "stock_quantity": 20,
                "top_notes": "Peach, Pear",
                "heart_notes": "Magnolia, Peony",
                "base_notes": "Amber, Musk",
                "is_featured": False,
                "is_bestseller": True,
                "is_active": True,
                "images": [
                    "https://images.unsplash.com/photo-1541643600914-78b084683601?w=800"
                ]
            },
            {
                "name": "Tester Sample",
                "category": categories_dict.get("Testers"),
                "concentration": "edp",
                "size_ml": 5,
                "description": "Sample tester for new arrivals.",
                "price": 5000.00,
                "stock_quantity": 10,
                "top_notes": "Bergamot",
                "heart_notes": "Lavender",
                "base_notes": "Cedarwood",
                "is_featured": False,
                "is_bestseller": False,
                "is_active": True,
                "images": [
                    "https://images.unsplash.com/photo-1590736969956-6d9c2a8d6972?w=800"
                ]
            }
        ]
        for prod in products:
            p, created = Product.objects.get_or_create(
                name=prod["name"],
                defaults={
                    "brand": brand,
                    "category": prod["category"],
                    "concentration": prod["concentration"],
                    "size_ml": prod["size_ml"],
                    "short_description": prod["description"],
                    "full_description": prod["description"],
                    "price": prod["price"],
                    "stock_quantity": prod["stock_quantity"],
                    "top_notes": prod["top_notes"],
                    "heart_notes": prod["heart_notes"],
                    "base_notes": prod["base_notes"],
                    "is_featured": prod["is_featured"],
                    "is_bestseller": prod["is_bestseller"],
                    "is_available": prod["is_active"]
                }
            )
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Exists'} product: {p.name}"))
            if created:
                for idx, img_url in enumerate(prod["images"]):
                    try:
                        result = urllib.request.urlopen(img_url)
                        img_data = result.read()
                        # Extract a filename from the URL or use a default
                        file_ext = img_url.split('.')[-1].split('?')[0]
                        file_name = f"{p.slug}-{idx+1}.{file_ext if file_ext in ['jpg','jpeg','png','webp'] else 'jpg'}"
                        image_file = ContentFile(img_data, name=file_name)
                        ProductImage.objects.create(
                            product=p,
                            image=image_file,
                            is_primary=(idx == 0)
                        )
                        self.stdout.write(self.style.SUCCESS(f"Added image for {p.name}: {file_name}"))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Failed to add image for {p.name}: {e}"))
