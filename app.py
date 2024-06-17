from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import os
from flask import request

app = Flask(__name__)
app.secret_key = '1234'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instagram.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(100))
    posts = db.relationship('Post', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(200), nullable=True)
    likes = db.relationship('Like', backref='post', lazy=True)
    favorites = db.relationship('Favorite', backref='post', lazy=True)
    reposts = db.relationship('Repost', backref='post', lazy=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Repost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

@app.route('/')
def home():
    if 'username' in session:
        posts = Post.query.all()
        return render_template('home.html', posts=posts)  
    else:
        return redirect(url_for('login'))




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password.')
    else:
        return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/post', methods=['GET', 'POST'])
def post():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['image']
        caption = request.form['caption']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            new_post = Post(user_id=session['user_id'], image=filename, caption=caption)
            db.session.add(new_post)
            db.session.commit()
        return redirect(url_for('home'))
    return render_template('post.html')

@app.route('/postprofilepic', methods=['POST'])
def postprofilepic():
    if 'username' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if 'image' in request.files:
            image = request.files["image"]
            if image.filename == "":
                return "No selected file"
            else:
                filename = "".join(image.filename.split())
                image.save(os.path.join("static", filename))
                full_path = os.path.join("static", filename)
                user.profile_picture = filename
                db.session.commit()
                return redirect(url_for('profile'))
        else:
            return "No image file uploaded"
    else:
        return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'username' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        posts = Post.query.filter_by(user_id=user_id).all()
        return render_template('profile.html', user=user, posts=posts)
    else:
        return redirect(url_for('login'))

@app.route('/other_profile/<username>')
def other_profile(username):
    user = User.query.filter_by(username=username).first()
    if user:
        posts = user.posts 
        return render_template('profile.html', user=user, posts=posts)
    else:
        flash("User not found")
        return redirect(url_for('/')) 



@app.route('/posts/<int:post_id>/like', methods=['POST'])
def like(post_id):
    if 'username' in session:
        post = Post.query.get(post_id)
        if post:
            new_like = Like(user_id=session['user_id'], post_id=post_id)
            db.session.add(new_like)
            db.session.commit()
            flash("Post liked successfully")
            return redirect(url_for('home'))
        else:
            flash("Post not found")
            return redirect(url_for('home'))
    else:
        flash("Unauthorized")
        return redirect(url_for('login'))

@app.route('/reposts')
def reposted_posts():
    if 'username' in session:
        user_id = session['user_id']
        reposted_posts = Post.query.join(Repost, Repost.post_id == Post.id).filter(Repost.user_id == user_id).all()
        return render_template('reposted_posts.html', reposted_posts=reposted_posts)
    else:
        flash("Unauthorized")
        return redirect(url_for('login'))

@app.route('/posts/<int:post_id>/repost', methods=['POST'])
def repost(post_id):
    if 'username' in session:
        post = Post.query.get(post_id)
        if post:
            new_repost = Repost(user_id=session['user_id'], post_id=post_id)
            db.session.add(new_repost)
            db.session.commit()
            flash("Post reposted successfully")
            return redirect(url_for('home'))
        else:
            flash("Post not found")
            return redirect(url_for('home'))
    else:
        flash("Unauthorized")
        return redirect(url_for('login'))

@app.route('/posts/<int:post_id>')
def view_post(post_id):
    post = Post.query.get(post_id)
    if post:
        return render_template('view_post.html', post=post)
    else:
        flash("Post not found")
        return redirect(url_for('home'))

@app.route('/posts/<int:post_id>/delete_repost', methods=['POST'])
def delete_repost(post_id):
    if 'username' in session:
        repost = Repost.query.filter_by(user_id=session['user_id'], post_id=post_id).first()
        if repost:
            db.session.delete(repost)
            db.session.commit()
            flash("Repost deleted successfully")
        else:
            flash("Repost not found")
    else:
        flash("Unauthorized")
    return redirect(url_for('reposted_posts'))

@app.route('/posts/<int:post_id>/delete_like', methods=['POST'])
def delete_like(post_id):
    if 'username' in session:
        like = Like.query.filter_by(user_id=session['user_id'], post_id=post_id).first()
        if like:
            db.session.delete(like)
            db.session.commit()
            flash("Like deleted successfully")
        else:
            flash("Like not found")
    else:
        flash("Unauthorized")
    return redirect(url_for('liked_photos'))

@app.route('/liked_photos')
def liked_photos():
    if 'username' in session:
        user_id = session['user_id']
        liked_posts = []
        user_likes = Like.query.filter_by(user_id=user_id).all()
        for like in user_likes:
            post = Post.query.filter_by(id=like.post_id).first()
            if post:
                liked_posts.append(post)
        return render_template('liked_photos.html', user=session['username'], liked_posts=liked_posts)
    else:
        flash("Unauthorized")
        return redirect(url_for('login'))

@app.route('/favorites')
def favorites():
    if 'username' in session:
        user_id = session['user_id']
        favorites = Favorite.query.filter_by(user_id=user_id).all()
        favorite_posts = [Post.query.get(favorite.post_id) for favorite in favorites]
        return render_template('favorite.html', favorites=favorite_posts)
    else:
        flash("Please login to view favorite posts")
        return redirect(url_for('login'))

@app.route('/add_to_favorite/<int:post_id>', methods=['POST'])
def add_to_favorite(post_id):
    if 'username' in session:
        user_id = session['user_id']
       
        favorite = Favorite.query.filter_by(user_id=user_id, post_id=post_id).first()
        if favorite:
            flash("Post already in favorites")
        else:
            
            new_favorite = Favorite(user_id=user_id, post_id=post_id)
            db.session.add(new_favorite)
            db.session.commit()
            flash("Post added to favorites")
        return redirect(url_for('favorites'))  
    else:
        flash("Please login to add to favorites")
        return redirect(url_for('login'))
        


@app.route('/delete_favorite/<int:post_id>', methods=['POST'])
def delete_favorite(post_id):
    if 'username' in session:
        user_id = session['user_id']
        favorite = Favorite.query.filter_by(user_id=user_id, post_id=post_id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            flash("Post removed from favorites")
        else:
            flash("Post not found in favorites")
        return redirect(url_for('home'))
    else:
        flash("Please login to delete a favorite post")
        return redirect(url_for('login'))

@app.route('/search_user', methods=['POST'])
def search_user():
    search = request.form["search"]
    search_users = User.query.filter_by(username=search).first()
    return render_template("search_results.html", search_users=search_users)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)




















                