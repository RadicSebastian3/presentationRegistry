from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    user_type = db.Column(db.String(20), nullable=False)  # 'student' or 'company'
    # Student specific fields
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    class_name = db.Column(db.String(50))
    # Company specific fields
    company_name = db.Column(db.String(100))
    is_approved = db.Column(db.Boolean, default=False)
    # Relationships
    registrations = db.relationship('Registration', backref='student', foreign_keys='Registration.student_id')

class Presentation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    image_url = db.Column(db.String(200))  # Store the path to the uploaded image
    max_students = db.Column(db.Integer, default=30)  # Maximum number of students
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company = db.relationship('User', backref='presentations')
    registrations = db.relationship('Registration', backref='presentation', cascade='all, delete-orphan')

    @property
    def available_spots(self):
        return self.max_students - len(self.registrations)

    @property
    def is_full(self):
        return len(self.registrations) >= self.max_students

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentation.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    presentations = Presentation.query.order_by(Presentation.datetime).all()
    return render_template('index.html', presentations=presentations)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken')
            return redirect(url_for('register'))
        
        user = User(username=username, user_type=user_type)
        user.password_hash = generate_password_hash(password)
        
        if user_type == 'student':
            user.first_name = request.form.get('first_name')
            user.last_name = request.form.get('last_name')
            user.class_name = request.form.get('class_name')
        elif user_type == 'company':
            access_key = request.form.get('access_key')
            if access_key != 'your_secret_key':
                flash('Invalid access key')
                return redirect(url_for('register'))
            user.company_name = request.form.get('company_name')
            user.is_approved = True
        
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/create_presentation', methods=['GET', 'POST'])
@login_required
def create_presentation():
    if current_user.user_type != 'company':
        flash('Only companies can create presentations')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        image = request.files.get('image')
        image_url = None
        
        if image and allowed_file(image.filename):
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{image.filename}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = f"uploads/{filename}"
        
        presentation = Presentation(
            title=request.form.get('title'),
            description=request.form.get('description'),
            datetime=datetime.strptime(request.form.get('datetime'), '%Y-%m-%dT%H:%M'),
            company_id=current_user.id,
            image_url=image_url,
            max_students=int(request.form.get('max_students', 30))
        )
        db.session.add(presentation)
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('create_presentation.html')

@app.route('/register_presentation/<int:presentation_id>')
@login_required
def register_presentation(presentation_id):
    if current_user.user_type != 'student':
        flash('Only students can register for presentations')
        return redirect(url_for('index'))
    
    presentation = Presentation.query.get_or_404(presentation_id)
    
    if presentation.is_full:
        flash('This presentation is already full')
        return redirect(url_for('index'))
    
    if Registration.query.filter_by(student_id=current_user.id, presentation_id=presentation_id).first():
        flash('Already registered for this presentation')
        return redirect(url_for('index'))
    
    registration = Registration(student_id=current_user.id, presentation_id=presentation_id)
    db.session.add(registration)
    db.session.commit()
    flash('Successfully registered for the presentation')
    return redirect(url_for('index'))

@app.route('/presentation/<int:presentation_id>')
@login_required
def view_presentation(presentation_id):
    presentation = Presentation.query.get_or_404(presentation_id)
    registrations = Registration.query.filter_by(presentation_id=presentation_id).all()
    return render_template('view_presentation.html', presentation=presentation, registrations=registrations)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 