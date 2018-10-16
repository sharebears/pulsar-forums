from werkzeug import find_modules, import_string

from forums import routes
from forums.modifications import modify_core


def init_app(app):
    with app.app_context():
        for name in find_modules('forums', recursive=True):
            import_string(name)
        app.register_blueprint(routes.bp)


modify_core()
