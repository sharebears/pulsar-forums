import json

import pytest

from conftest import add_permissions, check_json_response
from forums.models import ForumPost, ForumThread, ForumThreadSubscription


def test_view_thread(app, authed_client):
    add_permissions(app, 'forums_view')
    response = authed_client.get('/forums/threads/1')
    check_json_response(response, {'id': 1, 'topic': 'New Site'})
    assert response.status_code == 200


def test_view_thread_deleted(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_threads_modify_advanced')
    response = authed_client.get('/forums/threads/2')
    check_json_response(response, {'id': 2})
    assert response.status_code == 200


def test_view_thread_deleted_failure(app, authed_client):
    add_permissions(app, 'forums_view')
    response = authed_client.get('/forums/threads/2')
    check_json_response(response, 'ForumThread 2 does not exist.')
    assert response.status_code == 404


def test_view_thread_posts_include_dead(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_posts_modify_advanced')
    response = authed_client.get(
        '/forums/threads/5', query_string={'include_dead': True}
    )
    assert response.status_code == 200
    assert len(response.get_json()['response']['posts']) == 2


def test_view_thread_posts_include_dead_no_perm(app, authed_client):
    add_permissions(app, 'forums_view')
    response = authed_client.get(
        '/forums/threads/5', query_string={'include_dead': True}
    )
    assert response.status_code == 200
    assert len(response.get_json()['response']['posts']) == 1


def test_add_thread(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_threads_create')
    response = authed_client.post(
        '/forums/threads',
        data=json.dumps(
            {'topic': 'New Thread', 'forum_id': 5, 'contents': 'aabb'}
        ),
    )
    check_json_response(response, {'id': 6, 'topic': 'New Thread'})
    assert response.get_json()['response']['forum']['id'] == 5
    assert response.get_json()['response']['posts'][0]['contents'] == 'aabb'


def test_add_thread_nonexistent_category(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_threads_create')
    response = authed_client.post(
        '/forums/threads',
        data=json.dumps(
            {'topic': 'New Forum', 'forum_id': 100, 'contents': 'aa'}
        ),
    )
    check_json_response(response, 'Invalid Forum id.')


def test_add_thread_forum_subscriptions(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_threads_create')
    ForumThread.from_subscribed_user(user_id=1)  # cache
    response = authed_client.post(
        '/forums/threads',
        data=json.dumps(
            {'topic': 'New Thread', 'forum_id': 4, 'contents': 'aa'}
        ),
    )
    check_json_response(response, {'id': 6})
    assert response.get_json()['response']['forum']['id'] == 4
    assert {1, 2} == set(ForumThreadSubscription.user_ids_from_thread(6))
    assert 6 in {t.id for t in ForumThread.from_subscribed_user(user_id=1)}


def test_edit_thread(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_threads_modify')
    response = authed_client.put(
        '/forums/threads/1',
        data=json.dumps({'topic': 'Bite', 'forum_id': 4, 'locked': True}),
    )
    check_json_response(
        response, {'id': 1, 'topic': 'Bite', 'locked': True, 'sticky': False}
    )
    assert response.get_json()['response']['forum']['id'] == 4
    thread = ForumThread.from_pk(1)
    assert thread.id == 1
    assert thread.topic == 'Bite'
    assert thread.locked is True
    assert thread.sticky is False


def test_edit_thread_skips(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_threads_modify')
    response = authed_client.put(
        '/forums/threads/1', data=json.dumps({'sticky': True})
    )
    check_json_response(
        response,
        {'id': 1, 'topic': 'New Site', 'locked': False, 'sticky': True},
    )
    thread = ForumThread.from_pk(1)
    assert thread.sticky is True


def test_edit_thread_bad_category(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_threads_modify')
    response = authed_client.put(
        '/forums/threads/1', data=json.dumps({'forum_id': 100})
    )
    check_json_response(response, 'Invalid Forum id.')


def test_edit_thread_nonexistent(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_threads_modify')
    response = authed_client.put(
        '/forums/threads/100', data=json.dumps({'locked': True})
    )
    check_json_response(response, 'ForumThread 100 does not exist.')


def test_delete_thread(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_threads_modify_advanced')
    post = ForumPost.from_pk(
        3
    )  # Cache - post isn't deleted, belongs to thread
    response = authed_client.delete('/forums/threads/5')
    check_json_response(
        response, 'ForumThread 5 (Donations?) has been deleted.'
    )
    thread = ForumThread.from_pk(5, include_dead=True)
    assert thread.deleted
    post = ForumPost.from_pk(3, include_dead=True)
    assert post.deleted


def test_delete_thread_no_posts(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_threads_modify_advanced')
    response = authed_client.delete('/forums/threads/1')
    check_json_response(response, 'ForumThread 1 (New Site) has been deleted.')
    thread = ForumThread.from_pk(1, include_dead=True)
    assert thread.deleted


def test_delete_thread_nonexistent(app, authed_client):
    add_permissions(app, 'forums_view', 'forums_threads_modify_advanced')
    response = authed_client.delete('/forums/threads/100')
    check_json_response(response, 'ForumThread 100 does not exist.')


@pytest.mark.parametrize(
    'endpoint, method',
    [
        ('/forums/threads/1', 'GET'),
        ('/forums/threads/1', 'DELETE'),
        ('/forums/threads/1', 'PUT'),
        ('/forums/threads', 'POST'),
    ],
)
def test_route_permissions(app, authed_client, endpoint, method):
    response = authed_client.open(endpoint, method=method)
    check_json_response(
        response, 'You do not have permission to access this resource.'
    )
    assert response.status_code == 403
