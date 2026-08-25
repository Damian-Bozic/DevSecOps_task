import pytest

from app.repository import create_initial_products, products


@pytest.fixture(autouse=True)
def reset_products():
    products.clear()
    products.update(create_initial_products())
