from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_existing_product():
    response = client.get("/products/1")

    assert response.status_code == 200

    product = response.json()

    assert product["id"] == 1
    assert product["name"] == "Product 1"
    assert product["category"] == "Category 1"

def test_list_products():
    response = client.get("/products")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2000
    assert len(data["items"]) == 50
    assert data["limit"] == 50
    assert data["offset"] == 0

def test_list_products_with_pagination():
    response = client.get("/products?limit=5&offset=10")

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 5
    assert data["total"] == 2000
    assert data["limit"] == 5
    assert data["offset"] == 10
    assert data["items"][0]["id"] == 11

def test_get_nonexistent_product():
    response = client.get("/products/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}

def test_create_product():
    product_data = {
        "name": "Test Keyboard",
        "category": "Electronics",
        "price": 99.99,
    }

    response = client.post("/products", json=product_data)

    assert response.status_code == 201

    created_product = response.json()

    assert created_product["name"] == "Test Keyboard"
    assert created_product["category"] == "Electronics"
    assert created_product["price"] == 99.99
    assert "id" in created_product

def test_update_product():
    product_data = {
        "name": "Updated Keyboard",
        "category": "Updated Electronics",
        "price": 149.99,
    }

    response = client.put("/products/1", json=product_data)

    assert response.status_code == 200

    updated_product = response.json()

    assert updated_product["id"] == 1
    assert updated_product["name"] == "Updated Keyboard"
    assert updated_product["category"] == "Updated Electronics"
    assert updated_product["price"] == 149.99

def test_delete_product():
    response = client.delete("/products/2")

    assert response.status_code == 204

    response = client.get("/products/2")

    assert response.status_code == 404

def test_update_nonexistent_product():
    product_data = {
        "name": "Does Not Exist",
        "category": "Test",
        "price": 10.00,
    }

    response = client.put("/products/99999", json=product_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}

def test_delete_nonexistent_product():
    response = client.delete("/products/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}

def test_create_product_with_invalid_price():
    product_data = {
        "name": "Invalid Product",
        "category": "Test",
        "price": -10.00,
    }

    response = client.post("/products", json=product_data)

    assert response.status_code == 422

def test_create_product_with_missing_name():
    product_data = {
        "category": "Test",
        "price": 10.00,
    }

    response = client.post("/products", json=product_data)

    assert response.status_code == 422
