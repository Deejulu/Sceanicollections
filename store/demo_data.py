from store.models import Category, Product, Brand, ProductImage
from django.core.files.base import ContentFile
import urllib.request
from io import BytesIO

# 1. Add Categories
def add_categories():
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
        if created:
            print(f"Created category: {obj.name}")
        else:
            print(f"Category already exists: {obj.name}")

# 2. Add a Brand (required for Product FK)
def add_brand():
    brand, _ = Brand.objects.get_or_create(name="SceaniCollections", defaults={"description": "House brand for demo products."})
    return brand

# 3. Add Products with Images
def add_products():
    brand = add_brand()
    categories = {c.name: c for c in Category.objects.all()}
    products = [
        {
            "name": "Midnight Rose",
            "category": categories.get("Perfume Oils"),
            "concentration": "oil",
            "short_description": "A captivating blend of rose and bergamot with a sensual base of sandalwood and musk.",
            "price": 15000.00,
            "stock_quantity": 100,
            "top_notes": "Rose, Bergamot",
            "heart_notes": "Jasmine, Lily",
            "base_notes": "Sandalwood, Musk",
            "is_featured": True,
            "is_bestseller": True,
            "is_available": True,
            "images": [
                "https://images.unsplash.com/photo-1541643600914-78b084683601?w=800",
                "https://images.unsplash.com/photo-1590736969956-6d9c2a8d6972?w=800"
            ]
        },
        {
            "name": "Citrus Splash",
            "category": categories.get("Body Sprays"),
            "concentration": "edp",
            "short_description": "A fresh burst of citrus and florals for all-day energy.",
            "price": 8000.00,
            "stock_quantity": 80,
            "top_notes": "Lemon, Orange",
            "heart_notes": "Neroli, Jasmine",
            "base_notes": "Cedarwood, Musk",
            "is_featured": True,
            "is_bestseller": False,
            "is_available": True,
            "images": [
                "https://images.unsplash.com/photo-1590736969956-6d9c2a8d6972?w=800"
            ]
        },
        {
            "name": "Amber Oud",
            "category": categories.get("Eau de Parfum (EDP)"),
            "concentration": "edp",
            "short_description": "Rich amber and oud notes for a luxurious experience.",
            "price": 25000.00,
            "stock_quantity": 50,
            "top_notes": "Amber, Saffron",
            "heart_notes": "Oud, Rose",
            "base_notes": "Patchouli, Vanilla",
            "is_featured": True,
            "is_bestseller": True,
            "is_available": True,
            "images": [
                "https://images.unsplash.com/photo-1541643600914-78b084683601?w=800"
            ]
        },
        {
            "name": "Mini Discovery Set",
            "category": categories.get("Mini Sets"),
            "concentration": "oil",
            "short_description": "A set of mini perfume oils to discover your favorite scent.",
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
            "category": categories.get("Gift Sets"),
            "concentration": "edp",
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
            "category": categories.get("Testers"),
            "concentration": "edp",
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
        if created:
            print(f"Created product: {p.name}")
            for idx, img_url in enumerate(prod["images"]):
                try:
                    result = urllib.request.urlopen(img_url)
                    img_data = result.read()
                    image_file = ContentFile(img_data)
                    ProductImage.objects.create(
                        product=p,
                        image=image_file,
                        is_primary=(idx == 0)
                    )
                except Exception as e:
                    print(f"Failed to add image for {p.name}: {e}")
        else:
            print(f"Product already exists: {p.name}")

if __name__ == "__main__":
    add_categories()
    add_products()
