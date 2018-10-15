from conftest import add_permissions, check_json_response
from core import db
from forums.models import ForumSubscription, ForumThreadSubscription


def test_subscribe_to_forum(app, authed_client):
    add_permissions(app, 'modify_forum_subscriptions')
    response = authed_client.post('/subscriptions/forums/5')
    check_json_response(response, 'Successfully subscribed to forum 5.')
    assert ForumSubscription.from_attrs(user_id=1, forum_id=5)


def test_subscribe_to_forum_already_subscribed(app, authed_client):
    add_permissions(app, 'modify_forum_subscriptions')
    response = authed_client.post('/subscriptions/forums/2')
    check_json_response(response, 'You are already subscribed to forum 2.')


def test_unsubscribe_from_forum(app, authed_client):
    add_permissions(app, 'modify_forum_subscriptions')
    response = authed_client.delete('/subscriptions/forums/2')
    check_json_response(response, 'Successfully unsubscribed from forum 2.')
    assert not ForumSubscription.from_attrs(user_id=1, forum_id=2)


def test_unsubscribe_from_forum_not_subscribed(app, authed_client):
    add_permissions(app, 'modify_forum_subscriptions')
    response = authed_client.delete('/subscriptions/forums/5')
    check_json_response(response, 'You are not subscribed to forum 5.')


def test_subscribe_to_thread(app, authed_client):
    add_permissions(app, 'modify_forum_subscriptions')
    response = authed_client.post('/subscriptions/threads/5')
    check_json_response(response, 'Successfully subscribed to thread 5.')
    assert ForumThreadSubscription.from_attrs(user_id=1, thread_id=5)


def test_subscribe_to_thread_already_subscribed(app, authed_client):
    add_permissions(app, 'modify_forum_subscriptions')
    response = authed_client.post('/subscriptions/threads/3')
    check_json_response(response, 'You are already subscribed to thread 3.')


def test_unsubscribe_from_thread(app, authed_client):
    add_permissions(app, 'modify_forum_subscriptions')
    response = authed_client.delete('/subscriptions/threads/3')
    check_json_response(response, 'Successfully unsubscribed from thread 3.')
    assert not ForumThreadSubscription.from_attrs(user_id=1, thread_id=3)


def test_unsubscribe_from_thread_not_subscribed(app, authed_client):
    add_permissions(app, 'modify_forum_subscriptions')
    response = authed_client.delete('/subscriptions/threads/5')
    check_json_response(response, 'You are not subscribed to thread 5.')


def test_view_my_subscriptions(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/subscriptions/forums').get_json()['response']
    assert {1, 2, 4} == {s['id'] for s in response['forum_subscriptions']}
    assert {1, 3, 4} == {s['id'] for s in response['thread_subscriptions']}


def test_view_my_subscriptions_empty(app, authed_client):
    db.engine.execute("DELETE FROM forums_forums_subscriptions")
    db.engine.execute("DELETE FROM forums_threads_subscriptions")
    add_permissions(app, 'view_forums')
    response = authed_client.get('/subscriptions/forums').get_json()['response']
    assert response['forum_subscriptions'] == []
    assert response['thread_subscriptions'] == []


def test_view_my_subscriptions_no_forum_perms(app, authed_client):
    db.engine.execute("DELETE FROM forums_permissions")
    add_permissions(app, 'view_forums')
    response = authed_client.get('/subscriptions/forums').get_json()['response']
    assert response['forum_subscriptions'] == []
    assert response['thread_subscriptions'] == []
