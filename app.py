from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
from flask_jwt import JWT, jwt_required, current_identity
import os



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/Test'
app.config['SECRET_KEY'] = str(os.urandom(24).hex())
db = SQLAlchemy(app)


def authenticate(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user

def identity(payload):
    user_id = payload['identity']
    return User.query.get(user_id)

jwt = JWT(app, authenticate, identity)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def check_password(self, password):
        return self.password == password
    
    blog_posts = db.relationship('BlogPost', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, title, body, user_id):
        self.title = title
        self.body = body
        self.user_id = user_id


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)

    def __init__(self, body, user_id, post_id):
        self.body = body
        self.user_id = user_id
        self.post_id = post_id


db.create_all()

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required."}), 400
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({"error": "Username or email already exists."}), 409
    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully."}), 201


@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found."}), 404
    if not user.check_password(password):
        return jsonify({"error": "Invalid credentials."}), 401    
    token = jwt.encode({'identity': user.id}, app.config['SECRET_KEY'], algorithm='HS256') 
    return jsonify({"message": "Login successful.", "user_id": user.id, "token": token}), 200


@app.route('/api/posts', methods=['POST'])
@jwt_required()  
def create_blog_post():
    data = request.json
    title = data.get('title')
    body = data.get('body')

    if not title or not body:
        return jsonify({"error": "Title and body are required."}), 400
    user_id = current_identity.id 
    blog_post = BlogPost(title=title, body=body, user_id=user_id)
    db.session.add(blog_post)
    db.session.commit()

    return jsonify({"message": "Blog post created successfully.", "post_id": blog_post.id}), 201


@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()  
def post_comment(post_id):
    data = request.json
    body = data.get('body')
    if not body:
        return jsonify({"error": "Comment body is required."}), 400
    user_id = current_identity.id 
    comment = Comment(body=body, user_id=user_id, post_id=post_id)
    db.session.add(comment)
    db.session.commit()
    return jsonify({"message": "Comment posted successfully.", "comment_id": comment.id}), 201


if __name__ == '__main__':
    app.run(debug=True)






