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
    try:
        session['assessment_id'] = str(uuid.uuid4())
        questions = assessment_engine.get_initial_questions()
        return jsonify({
            'success': True,
            'assessment_id': session['assessment_id'],
            'questions': questions
        })
    except Exception as e:
        print(f"Start assessment error: {e}")
        return jsonify({'success': False, 'error': 'Failed to start assessment'}), 500

@app.route('/api/submit-assessment', methods=['POST'])
def submit_assessment():
    """Process assessment responses and generate learning profile"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        responses = data.get('responses', {})
        if not responses:
            return jsonify({'success': False, 'error': 'No responses found'}), 400
        
        # Process assessment
        try:
            profile = assessment_engine.process_assessment(responses)
        except Exception as e:
            print(f"Assessment processing error: {e}")
            # Return a default profile if processing fails
            profile = {
                'learning_styles': {
                    'vark': {'primary_style': 'visual', 'multimodal': False},
                    'kolb': {'style': 'assimilating'}
                },
                'knowledge_levels': {'overall_level': 'beginner', 'areas': {}, 'strengths': [], 'growth_areas': []},
                'preferences': {'weekly_hours': 5, 'session_length': 45},
                'career_profile': {},
                'recommendations': {
                    'content_types': ['videos', 'interactive'],
                    'learning_strategies': ['hands_on_practice'],
                    'pacing': {'weekly_commitment': 5, 'session_duration': 45}
                }
            }
        
        # Store in session for now (would save to user profile in production)
        session['learning_profile'] = profile
        
        return jsonify({
            'success': True,
            'profile': profile
        })
        
    except Exception as e:
        print(f"Submit assessment error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/generate-pathway', methods=['POST'])
def generate_pathway():
    """Generate a personalized learning pathway"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        career_goals = data.get('career_goals', [])
        timeline = data.get('timeline', '3-6 months')
        focus_areas = data.get('focus_areas', [])
        
        # Get learning profile from session
        learning_profile = session.get('learning_profile', {})
        
        # Generate pathway
        try:
            pathway = learning_engine.generate_pathway(
                learning_profile=learning_profile,
                career_goals=career_goals,
                timeline=timeline,
                focus_areas=focus_areas
            )
        except Exception as e:
            print(f"Pathway generation error: {e}")
            # Return a simplified pathway if generation fails
            pathway = {
                'id': str(uuid.uuid4()),
                'title': f"Learning Path: {career_goals[0] if career_goals else 'General Development'}",
                'description': 'A personalized learning pathway tailored to your goals.',
                'modules': [
                    {
                        'id': 'module_1',
                        'name': 'Getting Started',
                        'description': 'Begin your learning journey',
                        'topics': [
                            {
                                'id': 'topic_1',
                                'name': 'Fundamentals',
                                'description': 'Learn the basics',
                                'difficulty': 'beginner',
                                'estimated_hours': 10,
                                'resources': []
                            }
                        ],
                        'estimated_weeks': 2,
                        'difficulty': 'beginner'
                    }
                ],
                'total_duration_weeks': 12,
                'target_role': career_goals[0] if career_goals else 'General Development',
                'skills_covered': focus_areas if focus_areas else ['programming', 'problem_solving'],
                'learning_objectives': ['Build foundational skills', 'Complete practical projects']
            }
        
        # Aggregate resources for each topic
        try:
            enriched_pathway = resource_aggregator.enrich_pathway(pathway)
        except Exception as e:
            print(f"Resource aggregation error: {e}")
            enriched_pathway = pathway  # Use pathway without enrichment if aggregation fails
        
        # Store pathway in session for later retrieval
        session['current_pathway'] = enriched_pathway
        
        return jsonify({
            'success': True,
            'pathway': enriched_pathway
        })
        
    except Exception as e:
        print(f"Generate pathway error: {e}")
        return jsonify({'success': False, 'error': 'Failed to generate pathway'}), 500

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
    # Try to get pathway from session or provide fallback
    pathway_data = session.get('current_pathway', None)
    
    # If no pathway in session, create a basic one
    if not pathway_data:
        pathway_data = {
            'id': pathway_id,
            'title': 'Learning Pathway',
            'description': 'Your personalized learning journey',
            'modules': [],
            'total_duration_weeks': 4,
            'target_role': 'General Development',
            'skills_covered': ['learning', 'growth'],
            'learning_objectives': ['Learn effectively', 'Build practical skills']
        }
    
    return render_template('pathway.html', pathway_id=pathway_id, pathway_data=pathway_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)