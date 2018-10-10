import json

import pytest

from conftest import add_permissions, check_json_response
from pulsar.forums.models import Forum, ForumThread


def test_view_forum(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/forums/2')
    check_json_response(response, {
        'id': 2,
        'name': 'Bugs',
        'description': 'Squishy Squash',
        })
    assert response.status_code == 200


def test_view_forum_deleted(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.get('/forums/3')
    check_json_response(response, {
        'id': 3,
        'name': 'Bitsu Fan Club',
        })
    assert response.status_code == 200


def test_view_forum_deleted_fail(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/forums/3')
    check_json_response(response, 'Forum 3 does not exist.')
    assert response.status_code == 404


def test_view_forum_threads_include_dead(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_threads_advanced')
    response = authed_client.get('/forums/1', query_string={'include_dead': True})
    assert response.status_code == 200
    assert len(response.get_json()['response']['threads']) == 2


def test_view_forum_threads_include_dead_no_perm(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/forums/1', query_string={'include_dead': True})
    assert response.status_code == 200
    assert len(response.get_json()['response']['threads']) == 1


def test_add_forum(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.post('/forums', data=json.dumps({
        'name': 'New Forum',
        'category_id': 1,
        'description': 'New Description',
        'position': 99,
        }))
    check_json_response(response, {
        'id': 7,
        'name': 'New Forum',
        'description': 'New Description',
        })


def test_add_forum_nonexistent_category(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.post('/forums', data=json.dumps({
        'name': 'New Forum',
        'category_id': 100,
        }))
    check_json_response(response, 'Invalid ForumCategory id.')


def test_edit_forum(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.put('/forums/1', data=json.dumps({
        'name': 'Bite',
        'description': 'Very New Description',
        'category_id': 4,
        }))
    check_json_response(response, {
        'id': 1,
        'name': 'Bite',
        'description': 'Very New Description',
        })
    print(response.get_json())
    assert response.get_json()['response']['category']['id'] == 4
    forum = Forum.from_pk(1)
    assert forum.id == 1
    assert forum.name == 'Bite'
    assert forum.description == 'Very New Description'
    assert forum.category_id == 4


def test_edit_forum_skips(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.put('/forums/1', data=json.dumps({
        'position': 0,
        }))
    check_json_response(response, {
        'id': 1,
        'name': 'Pulsar',
        'description': 'Stuff about pulsar',
        'position': 0,
        })
    forum = Forum.from_pk(1)
    assert forum.position == 0


def test_edit_forum_bad_category(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.put('/forums/1', data=json.dumps({
        'category_id': 100,
        }))
    check_json_response(response, 'Invalid ForumCategory id.')


def test_edit_forum_nonexistent(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.put('/forums/100', data=json.dumps({
        'category_id': 10000,
        }))
    check_json_response(response, 'Forum 100 does not exist.')


def test_delete_forum(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    sub_thread = ForumThread.from_pk(5)  # Cache - thread isn't deleted, belongs to category
    response = authed_client.delete('/forums/5')
    check_json_response(response, 'Forum 5 (Yacht Funding) has been deleted.')
    forum = ForumThread.from_pk(5, include_dead=True)
    assert forum.deleted
    sub_thread = ForumThread.from_pk(5, include_dead=True)
    assert sub_thread.deleted


def test_delete_forum_nonexistent(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forums')
    response = authed_client.delete('/forums/100')
    check_json_response(response, 'Forum 100 does not exist.')


@pytest.mark.parametrize(
    'endpoint, method', [
        ('/forums/1', 'GET'),
        ('/forums', 'POST'),
    ])
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(response, 'You do not have permission to access this resource.')
    assert response.status_code == 403
