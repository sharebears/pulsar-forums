import json

import pytest
from voluptuous import Invalid

from conftest import add_permissions, check_json_response
from core import db
from core.permissions.models import UserPermission
from core.validators import PermissionsDict


def test_forum_permission_dict():
    data = {
        'forumaccess_forum_1': True,
        'forumaccess_thread_1': False
        }
    assert data == PermissionsDict()(data)


@pytest.mark.parametrize(
    'value', [
        {'forums_forums_permixsion_1': True},
        {'forumaccess_forum_1': 'False'},
        {'forumaccess_thread_a': True},
        'not-a-dict',
    ])
def test_forum_permission_dict_failure(value):
    with pytest.raises(Invalid):
        PermissionsDict()(value)


def test_change_forum_permissions(app, authed_client):
    db.engine.execute('DELETE FROM users_permissions')
    add_permissions(app, 'users_moderate', 'forumaccess_forum_1', 'forumaccess_thread_1')
    db.engine.execute("""UPDATE user_classes
                      SET permissions = '{"forumaccess_forum_2"}'""")

    response = authed_client.put('/users/1', data=json.dumps({
        'permissions': {
            'forumaccess_forum_2': False,
            'forumaccess_thread_1': False,
            'forumaccess_thread_2': True
        }})).get_json()

    print(response['response'])
    assert set(response['response']['forum_permissions']) == {
        'forumaccess_forum_1', 'forumaccess_thread_2'}

    f_perms = UserPermission.from_user(1, prefix='forumaccess')
    assert f_perms == {
        'forumaccess_forum_2': False,
        'forumaccess_forum_1': True,
        'forumaccess_thread_2': True,
        }


def test_change_forum_permissions_failure(app, authed_client):
    db.engine.execute('DELETE FROM users_permissions')
    add_permissions(app, 'users_moderate', 'forumaccess_thread_1')
    db.engine.execute("""UPDATE user_classes
                      SET permissions = '{"forumaccess_forum_2"}'""")

    response = authed_client.put('/users/1', data=json.dumps({
        'permissions': {
            'forumaccess_forum_2': True,
            'forumaccess_thread_1': False,
            'forumaccess_thread_4': False,
            'forumaccess_thread_2': True
        }}))

    check_json_response(
        response, 'The following permissions could not be added: forumaccess_forum_2. '
        'The following permissions could not be deleted: forumaccess_thread_4.')
    f_perms = UserPermission.from_user(1, prefix='forumaccess')
    assert f_perms == {'forumaccess_thread_1': True}
