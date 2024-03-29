import flask
from voluptuous import All, In, Length, Range, Schema

from core import db
from core.utils import require_permission, validate_data
from core.validators import BoolGET
from forums.models import Forum, ForumPost, ForumThread, ForumThreadNote

from . import bp

app = flask.current_app


VIEW_FORUM_THREAD_SCHEMA = Schema(
    {
        'page': All(int, Range(min=0, max=2147483648)),
        'limit': All(int, In((25, 50, 100))),
        'include_dead': BoolGET,
    }
)


@bp.route('/forums/threads/<int:id>', methods=['GET'])
@require_permission('forums_view')
@validate_data(VIEW_FORUM_THREAD_SCHEMA)
def view_thread(
    id: int, page: int = 1, limit: int = 50, include_dead: bool = False
) -> flask.Response:
    """
    This endpoint allows users to view details about a forum and its threads.

    .. :quickref: ForumThread; View a forum thread.

    **Example request**:

    .. parsed-literal::

       GET /forums/threads/1 HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. parsed-literal::

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": [
           {
           }
         ]
       }

    :>json list response: A forum thread

    :statuscode 200: View successful
    :statuscode 403: User does not have permission to view thread
    :statuscode 404: Thread does not exist
    """
    thread = ForumThread.from_pk(
        id,
        _404=True,
        include_dead=flask.g.user.has_permission(
            'forums_threads_modify_advanced'
        ),
    )
    thread.set_posts(
        page,
        limit,
        include_dead
        and flask.g.user.has_permission('forums_posts_modify_advanced'),
    )
    return flask.jsonify(thread)


CREATE_FORUM_THREAD_SCHEMA = Schema(
    {
        'topic': All(str, Length(max=150)),
        'forum_id': All(int, Range(min=0, max=2147483648)),
        'contents': All(str, Length(max=250000)),
    },
    required=True,
)


@bp.route('/forums/threads', methods=['POST'])
@require_permission('forums_threads_create')
@validate_data(CREATE_FORUM_THREAD_SCHEMA)
def create_thread(topic: str, forum_id: int, contents: str) -> flask.Response:
    """
    This is the endpoint for forum thread creation. The ``forums_threads_modify``
    permission is required to access this endpoint.

    .. :quickref: ForumThread; Create a forum thread.

    **Example request**:

    .. parsed-literal::

       POST /forums/threads HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "topic": "How do I get easy ration?",
         "forum_id": 4
       }

    **Example response**:

    .. parsed-literal::

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
         }
       }

    :>json dict response: The newly created forum thread

    :statuscode 200: Creation successful
    :statuscode 400: Creation unsuccessful
    """
    return flask.jsonify(
        ForumThread.new(
            topic=topic,
            forum_id=forum_id,
            creator_id=flask.g.user.id,
            post_contents=contents,
        )
    )


MODIFY_FORUM_THREAD_SCHEMA = Schema(
    {
        'topic': All(str, Length(max=150)),
        'forum_id': All(int, Range(min=0, max=2147483648)),
        'locked': BoolGET,
        'sticky': BoolGET,
    }
)


@bp.route('/forums/threads/<int:id>', methods=['PUT'])
@require_permission('forums_threads_modify')
@validate_data(MODIFY_FORUM_THREAD_SCHEMA)
def modify_thread(
    id: int,
    topic: str = None,
    forum_id: int = None,
    locked: bool = None,
    sticky: bool = None,
) -> flask.Response:
    """
    This is the endpoint for forum thread editing. The ``forums_threads_modify``
    permission is required to access this endpoint. The topic, forum_id,
    locked, and sticky attributes can be changed here.

    .. :quickref: ForumThread; Edit a forum thread.

    **Example request**:

    .. parsed-literal::

       PUT /forums/threads/6 HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "topic": "This does not contain typos.",
         "forum_id": 2,
         "locked": true,
         "sticky": false
       }


    **Example response**:

    .. parsed-literal::

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
         }
       }

    :>json dict response: The edited forum thread

    :statuscode 200: Editing successful
    :statuscode 400: Editing unsuccessful
    :statuscode 404: Forum thread does not exist
    """
    thread = ForumThread.from_pk(id, _404=True)
    if topic:
        thread.topic = topic
    if forum_id and Forum.is_valid(forum_id, error=True):
        thread.forum_id = forum_id
    if locked is not None:
        thread.locked = locked
    if sticky is not None:
        thread.sticky = sticky
    db.session.commit()
    return flask.jsonify(thread)


@bp.route('/forums/threads/<int:id>', methods=['DELETE'])
@require_permission('forums_threads_modify_advanced')
def delete_thread(id: int) -> flask.Response:
    """
    This is the endpoint for forum thread deletion . The ``forums_threads_modify_advanced``
    permission is required to access this endpoint. All posts in a deleted forum will also
    be deleted.

    .. :quickref: ForumThread; Delete a forum thread.

    **Example request**:

    .. parsed-literal::

       DELETE /forums/threads/2 HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

    **Example response**:

    .. parsed-literal::

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
         }
       }

    :>json dict response: The deleted forum thread

    :statuscode 200: Deletion successful
    :statuscode 400: Deletion unsuccessful
    :statuscode 404: Forum thread does not exist
    """
    thread = ForumThread.from_pk(id, _404=True)
    thread.deleted = True
    ForumPost.update_many(
        pks=ForumPost.get_ids_from_thread(thread.id), update={'deleted': True}
    )
    return flask.jsonify(
        f'ForumThread {id} ({thread.topic}) has been deleted.'
    )


ADD_FORUM_THREAD_NOTE_SCHEMA = Schema(
    {'note': All(str, Length(max=10000))}, required=True
)


@bp.route('/forums/threads/<int:id>/notes', methods=['POST'])
@require_permission('forums_threads_modify')
@validate_data(ADD_FORUM_THREAD_NOTE_SCHEMA)
def add_thread_note(id: int, note: str) -> flask.Response:
    """
    Endpoint for forum thread note creation. Limited to those with ``forums_threads_modify``
    permission.

    .. :quickref: ForumThreadNote; Add a forum thread note.

    **Example request**:

    .. parsed-literal::

       POST /forums/threads/1/notes HTTP/1.1

       {
         "note": "A note."
       }

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "<ForumThreadNote>"
       }

    :>json dict response: The forum note

    :statuscode 200: Deletion successful
    :statuscode 400: Invalid forum thread
    """
    return flask.jsonify(
        ForumThreadNote.new(thread_id=id, user_id=flask.g.user.id, note=note)
    )
