from __future__ import annotations
import importlib


def send_new_post_notification(post):
    main = importlib.import_module('main')
    db = main.db
    User = main.User
    with main.app.app_context():
        users = db.session.execute(db.select(User).where(User.notify_by_email == True)).scalars().all()
        for user in users:
            if user.id == post.author_id:
                continue
            body = f"A new post '{post.title}' has been published."
            main.send_email(user.email, "New Blog Post", body)


def send_comment_notification(comment):
    main = importlib.import_module('main')
    target = comment.post.author if comment.parent_id is None else comment.parent.author
    if not getattr(target, 'notify_by_email', True):
        return
    if target.id == comment.author_id:
        return
    body = f"New comment on '{comment.post.title}'."
    main.send_email(target.email, "New Comment", body)
