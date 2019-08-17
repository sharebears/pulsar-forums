import flask

from core import APIException, cache, db
from core.utils import require_permission
from forums.models import (
    Forum,
    ForumSubscription,
    ForumThread,
    ForumThreadSubscription,
)

from . import bp


@bp.route('/subscriptions/threads/<int:thread_id>', methods=['POST', 'DELETE'])
@require_permission('forums_subscriptions_modify')
def alter_thread_subscription(thread_id: int) -> flask.Response:
    """
    This is the endpoint for forum thread subscription. The ``forums_subscriptions_modify``
    permission is required to access this endpoint. A POST request creates a subscription,
    whereas a DELETE request removes a subscription.

    .. :quickref: ForumThreadSubscription; Subscribe to a forum thread.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "Successfully subscribed to thread 2."
       }

    :>json str response: Success or failure message

    :statuscode 200: Subscription alteration successful
    :statuscode 400: Subscription alteration unsuccessful
    :statuscode 404: Forum thread does not exist
    """
    thread = ForumThread.from_pk(thread_id, _404=True)
    subscription = ForumThreadSubscription.from_attrs(
        user_id=flask.g.user.id, thread_id=thread.id
    )
    if flask.request.method == 'POST':
        if subscription:
            raise APIException(
                f'You are already subscribed to thread {thread_id}.'
            )
        ForumThreadSubscription.new(
            user_id=flask.g.user.id, thread_id=thread_id
        )
        return flask.jsonify(f'Successfully subscribed to thread {thread_id}.')
    else:  # method = DELETE
        if not subscription:
            raise APIException(
                f'You are not subscribed to thread {thread_id}.'
            )
        db.session.delete(subscription)
        db.session.commit()
        cache.delete(
            ForumThreadSubscription.__cache_key_users__.format(
                thread_id=thread_id
            )
        )
        cache.delete(
            ForumThreadSubscription.__cache_key_of_user__.format(
                user_id=flask.g.user.id
            )
        )
        return flask.jsonify(
            f'Successfully unsubscribed from thread {thread_id}.'
        )


@bp.route('/subscriptions/forums/<int:forum_id>', methods=['POST', 'DELETE'])
@require_permission('forums_subscriptions_modify')
def alter_forum_subscription(forum_id: int) -> flask.Response:
    """
    This is the endpoint for forum subscription. The ``forums_subscriptions_modify``
    permission is required to access this endpoint. A POST request creates a subscription,
    whereas a DELETE request removes a subscription.

    .. :quickref: ForumSubscription; Subscribe to a forum.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "Successfully subscribed to forum 2."
       }

    :>json str response: Success or failure message

    :statuscode 200: Subscription alteration successful
    :statuscode 400: Subscription alteration unsuccessful
    :statuscode 404: Forum thread does not exist
    """
    forum = Forum.from_pk(forum_id, _404=True)
    subscription = ForumSubscription.from_attrs(
        user_id=flask.g.user.id, forum_id=forum.id
    )
    if flask.request.method == 'POST':
        if subscription:
            raise APIException(
                f'You are already subscribed to forum {forum_id}.'
            )
        ForumSubscription.new(user_id=flask.g.user.id, forum_id=forum_id)
        return flask.jsonify(f'Successfully subscribed to forum {forum_id}.')
    else:  # method = DELETE
        if not subscription:
            raise APIException(f'You are not subscribed to forum {forum_id}.')
        db.session.delete(subscription)
        db.session.commit()
        cache.delete(
            ForumSubscription.__cache_key_users__.format(forum_id=forum_id)
        )
        cache.delete(
            ForumSubscription.__cache_key_of_user__.format(
                user_id=flask.g.user.id
            )
        )
        return flask.jsonify(
            f'Successfully unsubscribed from forum {forum_id}.'
        )


@bp.route('/subscriptions/forums', methods=['GET'])
@require_permission('forums_view_subscriptions')
def view_forum_subscriptions() -> flask.Response:
    """
    This is the endpoint to view forum and thread subscriptions. The
    ``forums_view_subscriptions`` permission is required to access this endpoint.

    .. :quickref: ForumSubscription; View forum subscriptions.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": {
            "forum_subscriptions": [
              "<Forum>",
              "<Forum>"
            ],
            "thread_subscriptions": [
              "<ForumThread>",
              "<ForumThread>"
            ]
          }
        }

    :>json dict response: The forum and thread subscriptions

    :statuscode 200: The forum subscriptions
    """
    return flask.jsonify(Forum.from_subscribed_user(flask.g.user.id))


@bp.route('/subscriptions/threads', methods=['GET'])
@require_permission('forums_view_subscriptions')
def view_thread_subscriptions() -> flask.Response:
    """
    This is the endpoint to view forum and thread subscriptions. The
    ``forums_view_subscriptions`` permission is required to access this endpoint.

    .. :quickref: ForumSubscription; View forum subscriptions.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": [
              "<ForumThread>",
              "<ForumThread>"
            ]
          }
        }

    :>json dict response: The forum and thread subscriptions

    :statuscode 200: The forum subscriptions
    """
    return flask.jsonify(ForumThread.from_subscribed_user(flask.g.user.id))
