from core.mixins import Attribute, Serializer


class ForumCategorySerializer(Serializer):
    id = Attribute()
    name = Attribute()
    description = Attribute()
    position = Attribute()
    forums = Attribute(nested=False)
    deleted = Attribute(permission='forums_forums_modify')


class ForumSerializer(Serializer):
    id = Attribute()
    name = Attribute()
    description = Attribute()
    category = Attribute(nested=('id', 'name'))
    position = Attribute()
    thread_count = Attribute()
    threads = Attribute(nested=False)
    deleted = Attribute(permission='forums_forums_modify')
    last_updated_thread = Attribute()


class ForumThreadSerializer(Serializer):
    id = Attribute()
    topic = Attribute()
    forum = Attribute(nested=('id', ))
    poster = Attribute(nested=('id', 'username', ))
    locked = Attribute()
    sticky = Attribute()
    created_time = Attribute()
    poll = Attribute(nested=False)
    last_post = Attribute()
    last_viewed_post = Attribute()
    subscribed = Attribute()
    post_count = Attribute()
    posts = Attribute(nested=False)
    thread_notes = Attribute(permission='forums_threads_modify')
    deleted = Attribute(permission='forums_threads_modify_advanced')


class ForumPostSerializer(Serializer):
    id = Attribute()
    thread = Attribute(nested=('id', 'topic', ))
    poster = Attribute()
    contents = Attribute()
    time = Attribute()
    edited_time = Attribute()
    sticky = Attribute()
    editor = Attribute()
    deleted = Attribute(permission='forums_posts_modify_advanced', self_access=False)
    edit_history = Attribute(permission='forums_posts_modify_advanced', self_access=False)


class ForumPostEditHistorySerializer(Serializer):
    id = Attribute(permission='forums_posts_modify_advanced')
    editor = Attribute(permission='forums_posts_modify_advanced')
    contents = Attribute(permission='forums_posts_modify_advanced')
    time = Attribute(permission='forums_posts_modify_advanced')


class ForumThreadNoteSerializer(Serializer):
    id = Attribute(permission='forums_threads_modify')
    note = Attribute(permission='forums_threads_modify')
    user = Attribute(nested=('id', 'username'), permission='forums_threads_modify')
    time = Attribute(permission='forums_threads_modify')


class ForumPollSerializer(Serializer):
    id = Attribute()
    thread = Attribute(nested=('id', 'topic', ))
    question = Attribute()
    closed = Attribute()
    featured = Attribute()
    choices = Attribute()


class ForumPollChoiceSerializer(Serializer):
    id = Attribute()
    choice = Attribute()
    answers = Attribute()
