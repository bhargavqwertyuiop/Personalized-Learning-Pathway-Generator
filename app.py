from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import uuid
import os
from werkzeug.security import generate_password_hash, check_password_hash
from learning_engine import LearningPathwayEngine
from resource_aggregator import ResourceAggregator
from assessment_engine import AssessmentEngine

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_pathways.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Initialize core engines
learning_engine = LearningPathwayEngine()
resource_aggregator = ResourceAggregator()
assessment_engine = AssessmentEngine()

# Database Models
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Learning profile
    learning_style = db.Column(db.Text)  # JSON string
    career_goals = db.Column(db.Text)    # JSON string
    knowledge_level = db.Column(db.Text) # JSON string
    preferences = db.Column(db.Text)     # JSON string
    
    pathways = db.relationship('LearningPathway', backref='user', lazy=True)
    progress = db.relationship('Progress', backref='user', lazy=True)

class LearningPathway(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    curriculum = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    progress_entries = db.relationship('Progress', backref='pathway', lazy=True)

class Progress(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    pathway_id = db.Column(db.String(36), db.ForeignKey('learning_pathway.id'), nullable=False)
    resource_id = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='not_started')  # not_started, in_progress, completed
    completion_percentage = db.Column(db.Float, default=0.0)
    time_spent = db.Column(db.Integer, default=0)  # minutes
    notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/assessment')
def assessment():
    return render_template('assessment.html')

@app.route('/api/start-assessment', methods=['POST'])
def start_assessment():
    """Initialize a new assessment session"""
    session['assessment_id'] = str(uuid.uuid4())
    return jsonify({
        'success': True,
        'assessment_id': session['assessment_id'],
        'questions': assessment_engine.get_initial_questions()
    })

@app.route('/api/submit-assessment', methods=['POST'])
def submit_assessment():
    """Process assessment responses and generate learning profile"""
    data = request.json
    responses = data.get('responses', {})
    
    # Process assessment
    profile = assessment_engine.process_assessment(responses)
    
    # Store in session for now (would save to user profile in production)
    session['learning_profile'] = profile
    
    return jsonify({
        'success': True,
        'profile': profile
    })

@app.route('/api/generate-pathway', methods=['POST'])
def generate_pathway():
    """Generate a personalized learning pathway"""
    data = request.json
    career_goals = data.get('career_goals', [])
    timeline = data.get('timeline', '3-6 months')
    focus_areas = data.get('focus_areas', [])
    
    # Get learning profile from session
    learning_profile = session.get('learning_profile', {})
    
    # Generate pathway
    pathway = learning_engine.generate_pathway(
        learning_profile=learning_profile,
        career_goals=career_goals,
        timeline=timeline,
        focus_areas=focus_areas
    )
    
    # Aggregate resources for each topic
    enriched_pathway = resource_aggregator.enrich_pathway(pathway)
    
    return jsonify({
        'success': True,
        'pathway': enriched_pathway
    })

@app.route('/api/pathways/<pathway_id>/progress', methods=['POST'])
def update_progress():
    """Update progress on a specific resource"""
    data = request.json
    # Implementation for progress tracking
    return jsonify({'success': True})

@app.route('/api/adapt-pathway', methods=['POST'])
def adapt_pathway():
    """Adapt pathway based on user progress and feedback"""
    data = request.json
    pathway_id = data.get('pathway_id')
    feedback = data.get('feedback', {})
    
    # Get current progress
    # Analyze performance
    # Adapt pathway accordingly
    
    adapted_pathway = learning_engine.adapt_pathway(pathway_id, feedback)
    
    return jsonify({
        'success': True,
        'adapted_pathway': adapted_pathway
    })

@app.route('/dashboard')
def dashboard():
    """User dashboard showing all pathways and progress"""
    return render_template('dashboard.html')

@app.route('/pathway/<pathway_id>')
def pathway_view(pathway_id):
    """Detailed view of a specific learning pathway"""
    return render_template('pathway.html', pathway_id=pathway_id)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)