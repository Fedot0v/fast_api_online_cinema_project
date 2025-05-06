import pytest
from decimal import Decimal

from src.database.models.orders import OrderStatusEnum
from src.repositories.cart.cart_rep import CartRepository


async def create_order_with_movie(client, user_token, cart_repo, movie_id, user_id):
    try:
        await cart_repo.delete(user_id)
    except:
        pass
    
    await cart_repo.add_movie(user_id, movie_id)
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await client.post("/api/v1/orders/", headers=headers)
    assert response.status_code == 201
    return response.json()

@pytest.mark.asyncio
async def test_create_order_basic_flow(
    client,
    regular_user_token,
    db_session,
    test_movie,
    test_cart
):
    cart_repo = CartRepository(db_session)
    user_id = 1
    
    order = await create_order_with_movie(
        client,
        regular_user_token,
        cart_repo,
        test_movie.id,
        user_id
    )
    assert order["status"] == OrderStatusEnum.PENDING.value
    assert len(order["order_items"]) == 1
    assert order["order_items"][0]["movie_id"] == test_movie.id
    assert Decimal(order["total_amount"]) == test_movie.price
    assert order["user_id"] == user_id

@pytest.mark.asyncio
async def test_order_status_transitions(
    client,
    regular_user_token,
    admin_token,
    db_session,
    test_movie
):
    cart_repo = CartRepository(db_session)
    user_id = 1
    
    order = await create_order_with_movie(
        client,
        regular_user_token,
        cart_repo,
        test_movie.id,
        user_id
    )
    assert order["status"] == OrderStatusEnum.PENDING.value
    
    headers_user = {"Authorization": f"Bearer {regular_user_token}"}
    response = await client.post(
        f"/api/v1/orders/{order['id']}/cancel",
        headers=headers_user
    )
    assert response.status_code == 200
    
    order = await create_order_with_movie(
        client,
        regular_user_token,
        cart_repo,
        test_movie.id,
        user_id
    )
    assert order["status"] == OrderStatusEnum.PENDING.value
    
    response = await client.post(
        f"/api/v1/orders/{order['id']}/pay",
        headers=headers_user
    )
    assert response.status_code == 200
    
    response = await client.post(
        f"/api/v1/orders/{order['id']}/cancel",
        headers=headers_user
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_admin_order_listing(
    client,
    admin_token,
    regular_user_token,
    db_session,
    test_movie
):
    cart_repo = CartRepository(db_session)
    user_id = 2  # ID обычного пользователя
    
    order = await create_order_with_movie(
        client,
        regular_user_token,
        cart_repo,
        test_movie.id,
        user_id
    )
    
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/api/v1/orders/admin", headers=headers_admin)
    assert response.status_code == 200
    orders_list = response.json()
    assert len(orders_list) >= 1
    
    response = await client.get(
        "/api/v1/orders/admin",
        params={"status": OrderStatusEnum.PENDING.value},
        headers=headers_admin
    )
    assert response.status_code == 200
    filtered_orders = response.json()
    assert all(order["status"] == OrderStatusEnum.PENDING.value for order in filtered_orders)
    assert len(filtered_orders) >= 1 