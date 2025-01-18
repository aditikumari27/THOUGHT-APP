# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///thought_journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    interests = db.Column(db.String(200), nullable=True)
    thoughts = db.relationship('Thought', backref='author', lazy=True)

class Thought(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(100), nullable=True)
    shared = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    Name=db.Column(db.String(100), nullable=False)
    share_thought=db.Column(db.String(100), nullable=False) 

    

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')
   

@app.route('/thought', methods=['GET', 'POST'])
def thought():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image_file = request.files.get('image')
        image_filename = None
        if image_file:
            image_filename = image_file.filename
            save_path = f'static/uploads/{image_filename}'
            image_file.save(save_path)
            print(f"Image saved at: {save_path}")  # Debugging

        new_thought = Thought(
            title=title,
            content=content,
            image_path=image_filename,
            user_id=session['user_id']
        )
        db.session.add(new_thought)
        db.session.commit()
        flash('Thought added successfully!', 'success')
        return redirect(url_for('thought'))  # Redirect to the 'thought' route      
        flash('Thought added successfully!', 'success')
        return redirect(url_for('thought'))
    
    thoughts = Thought.query.all()
    
    return render_template('thought.html', thoughts=thoughts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('thought'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        phone_number = request.form.get('phone_number')
        interests = request.form.get('interests')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('signup'))
        
        new_user = User(
            email=email,
            password=password,
            phone_number=phone_number,
            interests=interests
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/review', methods=['GET', 'POST'])
def review():
    if request.method == 'POST':
        email = request.form['email']
        Name = request.form['Name']
        share_thought = request.form['share_thought']
        review = Review(email=email, Name=Name, share_thought=share_thought)
        db.session.add(review)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('review.html')

@app.route('/delete/<int:id>', methods=['POST', 'GET'])
def delete(id):
    thought = Thought.query.get_or_404(id)
    db.session.delete(thought)
    db.session.commit()
    return redirect(url_for('thought'))

@app.route('/update_thought/<int:id>', methods=['GET', 'POST'])
def update_thought(id):
    thought = Thought.query.get_or_404(id)
    
    if request.method == 'POST':
        # Update basic fields
        thought.title = request.form['title']
        thought.content = request.form['content']
        
        # Handle image update if provided
        image_file = request.files.get('image')
        if image_file and image_file.filename:  # Check if new image was uploaded
            # Create uploads directory if it doesn't exist
            uploads_dir = os.path.join('static', 'uploads')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{(image_file.filename)}"
            save_path = os.path.join(uploads_dir, filename)
            
            try:
                # Save the new image
                image_file.save(save_path)
                
                # Delete old image if it exists
                if thought.image_path:
                    old_image_path = os.path.join('static', 'uploads', thought.image_path)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                # Update image path in database
                thought.image_path = filename
                print(f"New image saved at: {save_path}")  # Debugging
                
            except Exception as e:
                print(f"Error saving image: {e}")  # Debugging
                # Handle the error appropriately
                flash('Error uploading image', 'error')
        
        try:
            # Commit all changes
            db.session.commit()
            flash('Thought updated successfully!', 'success')
            return redirect(url_for('thought'))
        except Exception as e:
            print(f"Error updating thought: {e}")  # Debugging
            db.session.rollback()
            flash('Error updating thought', 'error')
    
    return render_template('update.html', thought=thought)
    

# Create all database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)