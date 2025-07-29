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
        
        # Initialize user progress if not exists
        if 'user_progress' not in session:
            session['user_progress'] = {
                'completed_resources': [],
                'time_spent': 0,
                'pathways_created': 1,
                'skills_progress': {}
            }
        else:
            # Increment pathway creation count
            session['user_progress']['pathways_created'] = session['user_progress'].get('pathways_created', 0) + 1
        
        return jsonify({
            'success': True,
            'pathway': enriched_pathway
        })
        
    except Exception as e:
        print(f"Generate pathway error: {e}")
        return jsonify({'success': False, 'error': 'Failed to generate pathway'}), 500

@app.route('/api/pathways/<pathway_id>/progress', methods=['POST'])
def update_pathway_progress(pathway_id):
    """Update progress on a specific resource for a pathway"""
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
    # Calculate real progress data
    dashboard_data = calculate_dashboard_stats()
    return render_template('dashboard.html', **dashboard_data)

def calculate_dashboard_stats():
    """Calculate real user progress statistics"""
    # Get current pathway and learning profile
    current_pathway = session.get('current_pathway', None)
    learning_profile = session.get('learning_profile', None)
    user_progress = session.get('user_progress', {
        'completed_resources': [],
        'time_spent': 0,
        'pathways_created': 0,
        'skills_progress': {}
    })
    
    # Initialize stats
    stats = {
        'active_pathways': 0,
        'completed_modules': 0,
        'completed_resources': 0,
        'total_resources': 0,
        'time_spent': user_progress.get('time_spent', 0),
        'skills_mastered': 0,
        'recent_activity': [],
        'pathway_data': None,
        'learning_profile': learning_profile,
        'completion_percentage': 0
    }
    
    if current_pathway:
        stats['active_pathways'] = 1
        stats['pathway_data'] = current_pathway
        
        # Calculate module and resource statistics
        completed_modules = 0
        total_modules = len(current_pathway.get('modules', []))
        total_resources = 0
        completed_resources_count = 0
        
        for module in current_pathway.get('modules', []):
            module_completed = True
            module_resources = 0
            module_completed_resources = 0
            
            for topic in module.get('topics', []):
                topic_resources = topic.get('resources', [])
                module_resources += len(topic_resources)
                total_resources += len(topic_resources)
                
                for resource in topic_resources:
                    if resource.get('id') in user_progress.get('completed_resources', []):
                        module_completed_resources += 1
                        completed_resources_count += 1
            
            # Consider module completed if 80% of resources are done
            if module_resources > 0 and (module_completed_resources / module_resources) >= 0.8:
                completed_modules += 1
        
        stats['completed_modules'] = completed_modules
        stats['completed_resources'] = completed_resources_count
        stats['total_resources'] = total_resources
        
        # Calculate overall completion percentage
        if total_resources > 0:
            stats['completion_percentage'] = round((completed_resources_count / total_resources) * 100)
        
        # Calculate skills mastered (based on completed modules)
        skills_covered = current_pathway.get('skills_covered', [])
        if total_modules > 0:
            skills_completion_ratio = completed_modules / total_modules
            stats['skills_mastered'] = round(len(skills_covered) * skills_completion_ratio)
        
        # Generate recent activity
        stats['recent_activity'] = generate_recent_activity(current_pathway, user_progress)
    
    # Add pathway creation count
    if learning_profile:
        stats['pathways_created'] = user_progress.get('pathways_created', 1)
    
    return stats

def generate_recent_activity(pathway, user_progress):
    """Generate recent activity feed"""
    activities = []
    
    # Add pathway creation activity
    activities.append({
        'type': 'pathway_created',
        'title': f'Created learning pathway: {pathway.get("title", "Learning Journey")}',
        'description': f'Generated for {pathway.get("target_role", "skill development")}',
        'icon': 'fas fa-route',
        'color': 'primary',
        'time': 'Recently'
    })
    
    # Add skill progress activities
    completed_count = len(user_progress.get('completed_resources', []))
    if completed_count > 0:
        activities.append({
            'type': 'resources_completed',
            'title': f'Completed {completed_count} learning resources',
            'description': 'Keep up the great momentum!',
            'icon': 'fas fa-check-circle',
            'color': 'success',
            'time': 'This session'
        })
    
    # Add skills activities
    skills = pathway.get('skills_covered', [])
    if skills:
        activities.append({
            'type': 'skills_learning',
            'title': f'Learning {len(skills)} key skills',
            'description': ', '.join(skills[:3]) + ('...' if len(skills) > 3 else ''),
            'icon': 'fas fa-cogs',
            'color': 'info',
            'time': 'In progress'
        })
    
    return activities[:5]  # Return top 5 activities

# API endpoint to update progress
@app.route('/api/update-progress', methods=['POST'])
def update_progress():
    """Update user progress"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        resource_id = data.get('resource_id')
        action = data.get('action', 'complete')  # complete, uncomplete
        time_spent = data.get('time_spent', 0)
        
        # Get current progress
        user_progress = session.get('user_progress', {
            'completed_resources': [],
            'time_spent': 0,
            'pathways_created': 0,
            'skills_progress': {}
        })
        
        if action == 'complete' and resource_id not in user_progress['completed_resources']:
            user_progress['completed_resources'].append(resource_id)
        elif action == 'uncomplete' and resource_id in user_progress['completed_resources']:
            user_progress['completed_resources'].remove(resource_id)
        
        # Add time spent
        user_progress['time_spent'] += time_spent
        
        # Update session
        session['user_progress'] = user_progress
        
        return jsonify({'success': True, 'progress': user_progress})
        
    except Exception as e:
        print(f"Update progress error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-progress', methods=['GET'])
def get_progress():
    """Get current user progress"""
    try:
        user_progress = session.get('user_progress', {
            'completed_resources': [],
            'time_spent': 0,
            'pathways_created': 0,
            'skills_progress': {}
        })
        
        return jsonify({'success': True, 'progress': user_progress})
        
    except Exception as e:
        print(f"Get progress error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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