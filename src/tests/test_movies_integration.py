import pytest
from decimal import Decimal
from typing import Dict, Any

from src.database.models.movies import (
    MovieModel, CertificationModel, GenreModel,
    DirectorModel, StarModel
)


@pytest.mark.asyncio
async def test_movie_full_flow(client, admin_token, regular_user_token, db_session, test_certification):
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    movie_data = {
        "title": "New Test Movie",
        "year": 2024,
        "time": 120,
        "imdb": 8.0,
        "meta_score": 75.0,
        "description": "Test description",
        "price": 9.99,
        "certification_id": test_certification.id,
        "genre_ids": [],
        "director_ids": [],
        "star_ids": []
    }
    
    response = await client.post("/api/v1/movies/", json=movie_data, headers=headers_admin)
    assert response.status_code == 201
    movie = response.json()
    assert movie["title"] == movie_data["title"]
    assert movie["price"] == movie_data["price"]
    
    headers_user = {"Authorization": f"Bearer {regular_user_token}"}
    response = await client.get(f"/api/v1/movies/{movie['id']}", headers=headers_user)
    assert response.status_code == 200
    movie_details = response.json()
    assert movie_details["id"] == movie["id"]
    assert movie_details["title"] == movie_data["title"]
    
    update_data = {
        "title": "Updated Test Movie",
        "price": 14.99
    }
    response = await client.patch(
        f"/api/v1/movies/{movie['id']}",
        json=update_data,
        headers=headers_admin
    )
    assert response.status_code == 200
    updated_movie = response.json()
    assert updated_movie["title"] == update_data["title"]
    assert updated_movie["price"] == update_data["price"]
    
    response = await client.delete(f"/api/v1/movies/{movie['id']}", headers=headers_admin)
    assert response.status_code == 204
    
    response = await client.get(f"/api/v1/movies/{movie['id']}", headers=headers_user)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_movies_collection(client, admin_token, test_movie, regular_user_token, test_certification):
    headers_user = {"Authorization": f"Bearer {regular_user_token}"}
    
    response = await client.get("/api/v1/movies/", headers=headers_user)
    assert response.status_code == 200
    movies_list = response.json()
    assert len(movies_list) >= 1
    
    response = await client.get(
        "/api/v1/movies/",
        params={
            "filters": {
                "year": str(test_movie.year)
            }
        },
        headers=headers_user
    )
    assert response.status_code == 200
    filtered_movies = response.json()
    assert all(movie["year"] == test_movie.year for movie in filtered_movies)

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    movie_data = {
        "title": "Expensive Movie",
        "year": 2024,
        "time": 180,
        "imdb": 9.0,
        "meta_score": 85.0,
        "description": "Expensive movie description",
        "price": 19.99,
        "certification_id": test_certification.id,
        "genre_ids": [],
        "director_ids": [],
        "star_ids": []
    }
    response = await client.post("/api/v1/movies/", json=movie_data, headers=headers_admin)
    assert response.status_code == 201
    
    response = await client.get(
        "/api/v1/movies/",
        params={
            "sort_by": "price",
            "sort_order": "desc"
        },
        headers=headers_user
    )
    assert response.status_code == 200
    sorted_movies = response.json()
    assert len(sorted_movies) >= 2
    for i in range(len(sorted_movies) - 1):
        assert sorted_movies[i]["price"] >= sorted_movies[i + 1]["price"]


@pytest.mark.asyncio
async def test_movies_permissions(client, admin_token, regular_user_token, test_movie, test_certification):
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_user = {"Authorization": f"Bearer {regular_user_token}"}
    
    response = await client.get(f"/api/v1/movies/{test_movie.id}", headers=headers_user)
    assert response.status_code == 200

    movie_data = {
        "title": "User's Movie",
        "year": 2024,
        "time": 120,
        "imdb": 8.0,
        "meta_score": 75.0,
        "description": "Test description",
        "price": 9.99,
        "certification_id": test_certification.id,
        "genre_ids": [],
        "director_ids": [],
        "star_ids": []
    }
    response = await client.post("/api/v1/movies/", json=movie_data, headers=headers_user)
    assert response.status_code == 403

    update_data = {"title": "Updated by User"}
    response = await client.patch(
        f"/api/v1/movies/{test_movie.id}",
        json=update_data,
        headers=headers_user
    )
    assert response.status_code == 403
    

    response = await client.delete(f"/api/v1/movies/{test_movie.id}", headers=headers_user)
    assert response.status_code == 403
    

    response = await client.delete(f"/api/v1/movies/{test_movie.id}", headers=headers_admin)
    assert response.status_code == 204 
