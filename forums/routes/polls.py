from typing import Dict, List  # type: ignore

import flask
from voluptuous import Optional, Schema

from pulsar import APIException, cache, db
from pulsar.forums.models import ForumPoll, ForumPollAnswer, ForumPollChoice
from pulsar.utils import require_permission, validate_data
from pulsar.validators import BoolGET

from . import bp

app = flask.current_app


@bp.route('/forums/polls/<int:id>', methods=['GET'])
@require_permission('view_forums')
def view_poll(id: int) -> flask.Response:
    """
    This endpoint allows users to view details about a poll.

    .. :quickref: ForumPoll; View a forum poll.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": [
           "<ForumPoll>",
           "<ForumPoll>"
         ]
       }

    :>json list response: A forum poll

    :statuscode 200: View successful
    :statuscode 403: User does not have permission to view thread
    :statuscode 404: Thread does not exist
    """
    return flask.jsonify(ForumPoll.from_pk(id, error=True, _404=True))


MODIFY_FORUM_POLL_SCHEMA = Schema({
    'choices': Schema({
        Optional('add', default=[]): [str],
        Optional('delete', default=[]): [int],
        }),
    'closed': BoolGET,
    'featured': BoolGET,
    })


@bp.route('/forums/polls/<int:id>', methods=['PUT'])
@require_permission('modify_forum_polls')
@validate_data(MODIFY_FORUM_POLL_SCHEMA)
def modify_poll(id: int,
                choices: Dict[str, list] = None,
                closed: bool = None,
                featured: bool = None) -> flask.Response:
    """
    This is the endpoint for forum poll editing. The ``modify_forum_polls``
    permission is required to access this endpoint. The choices can be edited
    here, as well as the closed and featured statuses.

    .. :quickref: ForumPoll; Edit a forum poll.

    **Example request**:

    .. parsed-literal::

       PUT /forums/polls/6 HTTP/1.1

       {
         "id": 1,
         "choices": {
           "add": ["Yes", "No"],
           "delete": ["Placeholder1", "Placeholder2"]
         },
         "closed": true,
         "featured": false
       }


    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "<ForumPoll>"
       }

    :>json dict response: The edited forum poll

    :statuscode 200: Editing successful
    :statuscode 400: Editing unsuccessful
    :statuscode 404: Forum poll does not exist
    """
    poll = ForumPoll.from_pk(id, _404=True)
    if featured is not None:
        if featured is True:
            ForumPoll.unfeature_existing()
        poll.featured = featured
    if closed is not None:
        poll.closed = closed
    if choices:
        change_poll_choices(
            poll,
            choices['add'],
            choices['delete'])
    db.session.commit()
    return flask.jsonify(poll)


def change_poll_choices(poll: ForumPoll,
                        add: List[str],
                        delete: List[int]) -> None:
    """
    Change the choices to a poll. Create new choices or delete existing ones.
    The choices parameter should contain a dictionary of answer name keys and
    their status as booleans. True = Add, False = Delete.

    :param poll:    The forum poll to alter
    :param choices: The choices to edit
    """
    poll_choice_choices = {c.choice for c in poll.choices}
    poll_choice_ids = {c.id for c in poll.choices}
    errors = {
        'add': {choice for choice in add if choice in poll_choice_choices},
        'delete': {choice for choice in delete if choice not in poll_choice_ids}
        }

    error_message = []
    if errors['add']:
        error_message.append(
            f'The following poll choices could not be added: '  # type: ignore
            f'{", ".join(errors["add"])}.')
    if errors['delete']:
        error_message.append(
            f'The following poll choices could not be deleted: '  # type: ignore
            f'{", ".join([str(d) for d in errors["delete"]])}.')
    if error_message:
        raise APIException(' '.join(error_message))

    for choice in delete:
        choice = ForumPollChoice.from_pk(choice)
        choice.delete_answers()  # type: ignore
        db.session.delete(choice)
    for choice_new in add:
        db.session.add(ForumPollChoice(
            poll_id=poll.id,
            choice=choice_new))
    cache.delete(ForumPollChoice.__cache_key_of_poll__.format(poll_id=poll.id))
    poll.del_property_cache('choices')
    db.session.commit()


@bp.route('/forums/polls/choices/<int:choice_id>/vote', methods=['POST'])
@require_permission('forums_polls_vote')
def vote_on_poll(choice_id: int) -> flask.Response:
    """
    This is the endpoint for forum poll voting. The ``forums_polls_vote``
    permission is required to access this endpoint.

    .. :quickref: ForumPollChoice; Vote on a forum poll choice.

    **Example response**:

    .. parsed-literal::

       {
         "status": "success",
         "response": "You have successfully voted for choice 1032."
       }

    :>json str response: The result message

    :statuscode 200: Voting successful
    :statuscode 400: Voting unsuccessful
    :statuscode 404: Poll or poll choice
    """
    choice = ForumPollChoice.from_pk(choice_id, _404=True)
    if ForumPollAnswer.from_attrs(
            poll_id=choice.poll.id,
            user_id=flask.g.user.id):
        raise APIException('You have already voted on this poll.')
    ForumPollAnswer.new(
        poll_id=choice.poll.id,
        user_id=flask.g.user.id,
        choice_id=choice.id)
    return flask.jsonify(f'You have successfully voted for choice {choice.id}.')
