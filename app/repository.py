from app.models import Product


def create_initial_products() -> dict[int, Product]:
    return {
        product_id: Product(
            id=product_id,
            name=f"Product {product_id}",
            category=f"Category {product_id % 10}",
            price=round(product_id * 1.99, 2),
        )
        for product_id in range(1, 2001)
    }

products: dict[int, Product] = create_initial_products()