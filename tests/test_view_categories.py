import json

import pytest

from conftest import add_permissions, check_json_response
from pulsar.forums.models import ForumCategory


def test_view_categories(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/forums/categories')
    check_json_response(response, {
        'id': 1,
        'name': 'Site',
        'description': 'General site discussion',
        }, list_=True)
    assert response.status_code == 200
    assert len(response.get_json()['response']) == 3


def test_view_categories_include_dead(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.get('/forums/categories', query_string={'include_dead': True})
    assert response.status_code == 200
    assert len(response.get_json()['response']) == 4


def test_view_categories_include_dead_no_permissions(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/forums/categories', query_string={'include_dead': True})
    assert response.status_code == 200
    assert len(response.get_json()['response']) == 3


def test_add_category(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.post('/forums/categories', data=json.dumps({
        'name': 'New Forum',
        'description': 'New Description',
        'position': 99,
        }))
    check_json_response(response, {
        'id': 6,
        'name': 'New Forum',
        'description': 'New Description',
        'position': 99
        })


def test_edit_category(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.put('/forums/categories/1', data=json.dumps({
        'name': 'Bite',
        'description': 'Very New Description',
        }))
    check_json_response(response, {
        'id': 1,
        'name': 'Bite',
        'description': 'Very New Description',
        })
    category = ForumCategory.from_pk(1)
    assert category.id == 1
    assert category.name == 'Bite'
    assert category.description == 'Very New Description'


def test_edit_category_skips(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.put('/forums/categories/1', data=json.dumps({
        'position': 0,
        }))
    check_json_response(response, {
        'id': 1,
        'name': 'Site',
        'description': 'General site discussion',
        'position': 0,
        })
    category = ForumCategory.from_pk(1)
    assert category.position == 0


def test_delete_category(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.delete('/forums/categories/5')
    check_json_response(response, 'ForumCategory 5 (uWhatMate) has been deleted.')
    category = ForumCategory.from_pk(5, include_dead=True)
    assert category.deleted


def test_delete_category_with_forums(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.delete('/forums/categories/1')
    check_json_response(
        response, 'You cannot delete a forum category while it still has forums assigned to it.')


def test_delete_category_nonexistent(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.delete('/forums/categories/100')
    check_json_response(response, 'ForumCategory 100 does not exist.')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/forums/categories', 'GET'),
        ('/forums/categories', 'POST'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
