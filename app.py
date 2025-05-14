from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('posts', lazy=True))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    posts = Post.query.all()
    categories = Category.query.all()
    return render_template('home.html', posts=posts, categories=categories)

@app.route('/category/<int:category_id>')
def category(category_id):
    selected_category = Category.query.get_or_404(category_id)
    posts = Post.query.filter_by(category_id=category_id).all()
    categories = Category.query.all()
    return render_template('home.html', posts=posts, categories=categories, selected_category=selected_category)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Try a different one.', 'danger')
            return redirect(url_for('register'))
        password = generate_password_hash(request.form['password'])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    categories = Category.query.all()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category_id = int(request.form['category'])
        post = Post(title=title, content=content, author=current_user.username, category_id=category_id)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create_post.html', categories=categories)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.timestamp.desc()).all()
    if request.method == 'POST':
        if current_user.is_authenticated:
            comment = Comment(content=request.form['content'], author=current_user.username, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for('post_detail', post_id=post_id))
        else:
            flash('You must be logged in to comment.', 'warning')
            return redirect(url_for('login'))
    return render_template('post_detail.html', post=post, comments=comments)

if __name__ == '__main__':
    with app.app_context():
        if os.path.exists("blog.db"):
            os.remove("blog.db")
        db.create_all()
        if not Category.query.first():
            db.session.add_all([
                Category(name='Technology'),
                Category(name='Lifestyle'),
                Category(name='Tutorial')
            ])
            db.session.commit()
    app.run(debug=True)