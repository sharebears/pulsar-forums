from core.permissions import PermissionsEnum


class ForumPermissions(PermissionsEnum):
    VIEW = 'forums_view'
    CREATE_POST = 'forums_posts_create'
    MODIFY_POST = 'forums_posts_modify'
    DOUBLE_POST = 'forums_posts_double'
    POST_IN_LOCKED = 'forums_posts_in_locked'
    CREATE_THREAD = 'forums_threads_create'
    MODIFY_THREAD = 'forums_threads_modify'
    MODIFY_THREAD_ADVANCED = 'forums_threads_modify_advanced'
    MODIFY_SUBSCRIPTIONS = 'forums_subscriptions_modify'
    MODIFY_FORUMS = 'forums_forums_modify'
    MODIFY_POLLS = 'forums_polls_vote'
    VIEW_SUBSCRIPTIONS = 'forums_view_subscriptions'
