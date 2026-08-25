from fastapi import FastAPI, HTTPException, Query
from app.models import Product, ProductCreate, ProductUpdate
from app.repository import products

app = FastAPI(
    title="DevSecOps CRUD API",
    version="1.0.0",
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/products")
def list_products(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    all_products = list(products.values())

    paginated_products = all_products[offset : offset + limit]

    return {
        "items": paginated_products,
        "total": len(all_products),
        "limit": limit,
        "offset": offset,
    }

@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = products.get(product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product

@app.post("/products", status_code=201)
def create_product(product_data: ProductCreate):
    new_id = max(products.keys()) + 1

    product = Product(
        id=new_id,
        **product_data.model_dump(),
    )

    products[new_id] = product

    return product

@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    product_data: ProductUpdate,
):
    if product_id not in products:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    updated_product = Product(
        id=product_id,
        **product_data.model_dump(),
    )

    products[product_id] = updated_product

    return updated_product

@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int):
    if product_id not in products:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    del products[product_id]