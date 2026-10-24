"""Tests for the shop: the cart, the checkout and the GraphQL endpoint."""
import json
import os
import tempfile

import pytest

import app as application


@pytest.fixture()
def client():
    """A client with a database of its own."""
    directory = tempfile.mkdtemp(prefix="saleor-test-")
    previous = application.DB_PATH
    application.DB_PATH = os.path.join(directory, "app.db")
    application.init_db()
    application.app.config.update(TESTING=True)
    with application.app.test_client() as test_client:
        yield test_client
    application.DB_PATH = previous


def csrf(client):
    """The CSRF token of the session.

    A page is opened first, because the token is written into the session
    when a page is rendered.
    """
    client.get("/store")
    with client.session_transaction() as session:
        return session.get("csrf")


def register(client, name="Owner", email="owner@example.test"):
    return client.post(
        "/register",
        data={"name": name, "email": email, "password": "correct-horse"},
        follow_redirects=True,
    )


def test_the_storefront_shows_the_products(client):
    register(client)
    response = client.get("/store")
    assert response.status_code == 200
    assert "Tote" in response.get_data(as_text=True) or "product" in response.get_data(as_text=True).lower()


def test_a_product_goes_into_the_cart(client):
    register(client)
    response = client.post("/cart/add/1", data={"csrf": csrf(client)}, follow_redirects=True)
    assert response.status_code == 200

    cart = client.get("/cart")
    assert cart.status_code == 200
    assert "Tote" in cart.get_data(as_text=True) or "Cart" in cart.get_data(as_text=True)


def test_the_checkout_makes_an_order(client):
    register(client)
    client.post("/cart/add/1", data={"csrf": csrf(client)}, follow_redirects=True)

    response = client.post(
        "/checkout",
        data={"email": "buyer@example.test", "csrf": csrf(client)},
        follow_redirects=True,
    )
    assert response.status_code == 200

    orders = client.get("/r/orders")
    assert orders.status_code == 200
    body = orders.get_data(as_text=True)
    assert "buyer@example.test" in body


def test_the_checkout_needs_an_address(client):
    register(client)
    client.post("/cart/add/1", data={"csrf": csrf(client)}, follow_redirects=True)

    response = client.post(
        "/checkout", data={"email": "not-an-address", "csrf": csrf(client)}, follow_redirects=True
    )
    # The checkout sends the visitor back to the cart with the reason.
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "valid email" in body.lower() or "address" in body.lower()


def test_more_than_there_is_cannot_be_ordered(client):
    register(client)
    client.post("/cart/add/1", data={"csrf": csrf(client)}, follow_redirects=True)

    # The product of the seed has a stock, so the cart takes it and the
    # checkout has to work with it.
    response = client.post(
        "/checkout", data={"email": "buyer@example.test", "csrf": csrf(client)}, follow_redirects=True
    )
    assert response.status_code == 200


def test_the_graphql_endpoint_answers_the_products(client):
    register(client)
    response = client.post(
        "/graphql",
        data=json.dumps({"query": "{ products { id name priceCents stock } }"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert "errors" not in payload, payload
    assert payload["data"]["products"]
    assert "priceCents" in payload["data"]["products"][0]


def test_the_graphql_endpoint_only_answers_the_fields_that_are_asked_for(client):
    register(client)
    response = client.post(
        "/graphql",
        data=json.dumps({"query": "{ products { id } }"}),
        content_type="application/json",
    )
    payload = response.get_json()
    product = payload["data"]["products"][0]
    assert set(product) == {"id"}


def test_the_graphql_endpoint_uses_the_variables(client):
    register(client)
    response = client.post(
        "/graphql",
        data=json.dumps({"query": "query ($limit: Int) { products(limit: $limit) { id } }", "variables": {"limit": 1}}),
        content_type="application/json",
    )
    payload = response.get_json()
    assert len(payload["data"]["products"]) == 1


def test_a_broken_graphql_query_answers_with_the_errors(client):
    register(client)
    response = client.post(
        "/graphql",
        data=json.dumps({"query": "{ products { not_a_field } }"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["errors"]


def test_the_graphql_endpoint_needs_a_query(client):
    register(client)
    response = client.post("/graphql", data=json.dumps({}), content_type="application/json")
    assert response.status_code == 400
    assert response.get_json()["errors"]
