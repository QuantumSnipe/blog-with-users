from datetime import date, datetime
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Boolean, ForeignKey, DateTime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, CreatePostForm, LoginForm, CommentForm
from typing import List
import os
from dotenv import find_dotenv, load_dotenv
import smtplib


dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# Admin-only decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Only admins can access this page.')
            return redirect(url_for('get_all_posts'))
        return f(*args, **kargs)
    return decorated_function


# CREATE DATABASE
class Base(DeclarativeBase):
    pass
db_uri = os.getenv("DATABASE_URL")
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)



# CONFIGURE TABLES 
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String(100))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    posts = relationship('BlogPost', back_populates='author')
    comments = relationship('Comment', back_populates='author')


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    author = relationship('User', back_populates='posts')
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments = relationship('Comment', back_populates='post', cascade='all, delete-orphan')


class Comment(db.Model):
    __tablename__ = 'comments'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey('blog_posts.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('comments.id'), nullable=True)
    parent = relationship('Comment', remote_side='Comment.id', back_populates='replies')
    replies = relationship('Comment', back_populates='parent', cascade='all, delete-orphan')
    author = relationship('User', back_populates='comments')
    post = relationship('BlogPost', back_populates='comments')

    

with app.app_context():
    db.create_all()

# Routes
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Hash the user's password when creating a new user.
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if existing_user:
            flash('Email already registered. Log in instead!')
            return redirect(url_for('login'))
        
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        user_count = db.session.query(User).count()
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
            is_admin=(user_count == 0)
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user) 
        return redirect(url_for("get_all_posts"))
    
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        if not user:
            flash("That email does not exist, please try again.")
        elif not check_password_hash(user.password, password=password):
            flash("Password incorrect, please try again.")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
        
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost).order_by(BlogPost.date.desc())).scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    form = CommentForm()
    parent_id = request.form.get('parent_id')
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to log in or register to comment.")
        
        comment = Comment(
            content=form.comment_text.data,
            author_id=current_user.id, 
            post_id=post_id,
            parent_id=int(parent_id) if parent_id else None
        )
        db.session.add(comment)
        db.session.commit()
        flash("Comment added successfully.")
        return redirect(url_for('show_post', post_id=post_id))
    
    comments = db.session.execute(db.select(Comment).where(Comment.post_id == post_id, Comment.parent_id == None).order_by(Comment.created_at.desc())).scalars().all()
    return render_template("post.html", post=requested_post, current_user=current_user,form=form,comments=comments)


@app.route("/new-post", methods=["GET", "POST"])
@login_required
@admin_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author_id = current_user.id
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>")
@login_required
@admin_required
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/delete-comment/<int:comment_id>")
@login_required
def delete_comment(comment_id):
    comment = db.get_or_404(Comment,comment_id)
    if comment.author_id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted successfully.")
    return redirect(url_for("show_post", post_id=comment.post_id))

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

MAIL_ADDRESS = os.getenv('MAIL_ADDRESS')
MAIL_APP_PW = os.getenv('MAIL_APP_PW')

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        send_email(
            to_addr=MAIL_ADDRESS,
            subject=f"Message from {name} <{email}>",
            body=message
        )
        flash("Thanks! Your note is on its way.")
        return redirect(url_for("contact"))
    
    return render_template("contact.html")

def send_email(to_addr: str, subject: str, body: str):
    email_message = f"Subject:{subject}\n\n{body}"
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(MAIL_ADDRESS, MAIL_APP_PW)
        connection.sendmail(MAIL_ADDRESS, to_addr, email_message)



if __name__ == "__main__":
    app.run(debug=True, port=5002)
