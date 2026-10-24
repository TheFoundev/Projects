"""The GraphQL schema of the shop.

The schema is built over the SQLite tables of the application, so the
endpoint answers real GraphQL: the query is parsed, the fields that are
asked for are the ones that are read, and the variables are used.
"""
from __future__ import annotations

from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    GraphQLInt,
)

from app import get_db


def _product(row):
    """A product with the names that the schema uses.

    The columns of the table are named `price_cents`, the fields of the
    schema are named `priceCents`, so the row is mapped before it is
    answered.
    """
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "priceCents": row["price_cents"],
        "stock": row["stock"],
        "category": row["category"],
    }


def _order(row):
    """An order with the names that the schema uses."""
    return {
        "id": row["id"],
        "email": row["customer_email"],
        "totalCents": row["total_cents"],
        "status": row["status"],
        "createdAt": row["created_at"],
    }


def _products(_root, _info, limit=50):
    db = get_db()
    rows = db.execute("SELECT * FROM products ORDER BY id LIMIT ?", (int(limit),)).fetchall()
    return [_product(row) for row in rows]


def _orders(_root, _info):
    db = get_db()
    rows = db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    return [_order(row) for row in rows]


def _channels(_root, _info):
    db = get_db()
    rows = db.execute("SELECT * FROM channels ORDER BY id").fetchall()
    return [dict(row) for row in rows]


PRODUCT_TYPE = GraphQLObjectType(
    "Product",
    fields=lambda: {
        "id": GraphQLField(GraphQLInt),
        "name": GraphQLField(GraphQLString),
        "description": GraphQLField(GraphQLString),
        "priceCents": GraphQLField(GraphQLInt),
        "stock": GraphQLField(GraphQLInt),
        "category": GraphQLField(GraphQLString),
    },
)

ORDER_TYPE = GraphQLObjectType(
    "Order",
    fields=lambda: {
        "id": GraphQLField(GraphQLInt),
        "email": GraphQLField(GraphQLString),
        "totalCents": GraphQLField(GraphQLInt),
        "status": GraphQLField(GraphQLString),
        "createdAt": GraphQLField(GraphQLString),
    },
)

CHANNEL_TYPE = GraphQLObjectType(
    "Channel",
    fields=lambda: {
        "id": GraphQLField(GraphQLInt),
        "name": GraphQLField(GraphQLString),
        "description": GraphQLField(GraphQLString),
    },
)

QUERY_TYPE = GraphQLObjectType(
    "Query",
    fields=lambda: {
        "products": GraphQLField(
            GraphQLList(GraphQLNonNull(PRODUCT_TYPE)),
            args={"limit": GraphQLArgument(GraphQLInt, default_value=50)},
            resolve=_products,
        ),
        "orders": GraphQLField(GraphQLList(GraphQLNonNull(ORDER_TYPE)), resolve=_orders),
        "channels": GraphQLField(GraphQLList(GraphQLNonNull(CHANNEL_TYPE)), resolve=_channels),
    },
)

SCHEMA = GraphQLSchema(query=QUERY_TYPE)
