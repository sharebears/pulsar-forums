from typing import Optional as Optional_
from typing import Union

import flask
from voluptuous import All, Any, In, Length, Optional, Range, Schema

from pulsar import db
from pulsar.forums.models import Forum, ForumCategory, ForumThread
from pulsar.utils import require_permission, validate_data
from pulsar.validators import BoolGET

from . import bp

app = flask.current_app


VIEW_FORUM_SCHEMA = Schema({
    'page': All(int, Range(min=0, max=2147483648)),
    'limit': All(int, In((25, 50, 100))),
    'include_dead': BoolGET
    })


@bp.route('/forums/<int:id>', methods=['GET'])
@require_permission('view_forums')
@validate_data(VIEW_FORUM_SCHEMA)
def view_forum(id: int,
               page: int = 1,
               limit: int = 50,
               include_dead: bool = False) -> flask.Response:
    """
    This endpoint allows users to view details about a forum and its threads.

    .. :quickref: Forum; View a forum.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": [
           "<Forum>",
           "<Forum>"
         ]
       }

    :>json list response: A list of forums

    :statuscode 200: View successful
    :statuscode 403: User does not have permission to view forum
    :statuscode 404: Forum does not exist
    """
    forum = Forum.from_pk(
        id,
        _404=True,
        include_dead=flask.g.user.has_permission('modify_forums'))
    forum.set_threads(
        page,
        limit,
        include_dead and flask.g.user.has_permission('modify_forum_threads_advanced'))
    return flask.jsonify(forum)


CREATE_FORUM_SCHEMA = Schema({
    'name': All(str, Length(max=32)),
    'category_id': All(int, Range(min=0, max=2147483648)),
    Optional('description', default=None): Any(All(str, Length(max=1024)), None),
    Optional('position', default=0): All(int, Range(min=0, max=99999)),
    }, required=True)


@bp.route('/forums', methods=['POST'])
@require_permission('modify_forums')
@validate_data(CREATE_FORUM_SCHEMA)
def create_forum(name: str,
                 category_id: int,
                 description: str = None,
                 position: int = 0) -> flask.Response:
    """
    This is the endpoint for forum creation. The ``modify_forums`` permission
    is required to access this endpoint.

    .. :quickref: Forum; Create a forum.

    **Example request**:

    .. parsed-literal::

       POST /forums HTTP/1.1

       {
         "name": "Support",
         "description": "The place for confused share bears.",
         "position": 6
       }

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "<Forum>"
       }

    :>json dict response: The newly created forum

    :statuscode 200: Creation successful
    :statuscode 400: Creation unsuccessful
    """
    forum = Forum.new(
        name=name,
        category_id=category_id,
        description=description,
        position=position)
    return flask.jsonify(forum)


MODIFY_FORUM_SCHEMA = Schema({
    'name': All(str, Length(max=32)),
    'category_id': All(int, Range(min=0, max=2147483648)),
    'description': Any(All(str, Length(max=1024)), None),
    'position': All(int, Range(min=0, max=99999)),
    })


@bp.route('/forums/<int:id>', methods=['PUT'])
@require_permission('modify_forums')
@validate_data(MODIFY_FORUM_SCHEMA)
def modify_forum(id: int,
                 name: Optional_[str] = None,
                 category_id: Optional_[int] = None,
                 description: Union[str, bool, None] = False,
                 position: Optional_[int] = None) -> flask.Response:
    """
    This is the endpoint for forum editing. The ``modify_forums`` permission
    is required to access this endpoint. The name, category, description,
    and position of a forum can be changed here.

    .. :quickref: Forum; Edit a forum.

    **Example request**:

    .. parsed-literal::

       PUT /forums/6 HTTP/1.1

       {
         "name": "Support",
         "description": "The place for **very** confused share bears.",
         "position": 99
       }


    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "<Forum>"
       }

    :>json dict response: The edited forum

    :statuscode 200: Editing successful
    :statuscode 400: Editing unsuccessful
    :statuscode 404: Forum does not exist
    """
    forum = Forum.from_pk(id, _404=True)
    if name:
        forum.name = name
    if category_id and ForumCategory.is_valid(category_id, error=True):
        forum.category_id = category_id
    if description is not False:
        assert not isinstance(description, bool)
        forum.description = description
    if position is not None:
        forum.position = position
    db.session.commit()
    return flask.jsonify(forum)


@bp.route('/forums/<int:id>', methods=['DELETE'])
@require_permission('modify_forums')
def delete_forum(id: int) -> flask.Response:
    """
    This is the endpoint for forum deletion . The ``modify_forums`` permission
    is required to access this endpoint. All threads in a deleted forum will also
    be deleted.

    .. :quickref: Forum; Delete a forum.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "Forum 1 (Pulsar) has been deleted."
       }

    :>json str response: The deleted forum message

    :statuscode 200: Deletion successful
    :statuscode 400: Deletion unsuccessful
    :statuscode 404: Forum does not exist
    """
    forum = Forum.from_pk(id, _404=True)
    forum.deleted = True
    ForumThread.update_many(
        pks=ForumThread.get_ids_from_forum(forum.id),
        update={'deleted': True})
    return flask.jsonify(f'Forum {id} ({forum.name}) has been deleted.')
