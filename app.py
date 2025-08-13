from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import uuid
import os
from werkzeug.security import generate_password_hash, check_password_hash
from learning_engine import LearningPathwayEngine
from resource_aggregator import ResourceAggregator
from assessment_engine import AssessmentEngine

# Auth helpers
from functools import wraps

def is_authenticated() -> bool:
    return bool(session.get('user_id'))

def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login', next=request.path))
        return view_func(*args, **kwargs)
    return wrapper

def api_login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return view_func(*args, **kwargs)
    return wrapper

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
    if not is_authenticated():
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        if not username or not email or not password:
            return render_template('signup.html', error='All fields are required.')
        # Check existing user
        if User.query.filter((User.username == username) | (User.email == email)).first():
            return render_template('signup.html', error='Username or email already exists.')
        # Create user
        user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email.lower())).first()
        if not user or not check_password_hash(user.password_hash, password):
            return render_template('login.html', error='Invalid credentials.')
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/assessment')
@login_required
def assessment():
    return render_template('assessment.html')

@app.route('/api/start-assessment', methods=['POST'])
@api_login_required
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
@api_login_required
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
        
        # Store in session and persist for logged-in users
        session['learning_profile'] = profile

        user_id = session.get('user_id')
        if user_id:
            try:
                user = User.query.get(user_id)
                if user:
                    user.learning_style = json.dumps(profile.get('learning_styles', {}))
                    user.knowledge_level = json.dumps(profile.get('knowledge_levels', {}))
                    user.preferences = json.dumps(profile.get('preferences', {}))
                    user.career_goals = json.dumps(profile.get('career_profile', {}))
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"DB save profile error: {e}")
        
        return jsonify({
            'success': True,
            'profile': profile
        })
        
    except Exception as e:
        print(f"Submit assessment error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/generate-pathway', methods=['POST'])
@api_login_required
def generate_pathway():
    """Generate a personalized learning pathway"""
    try:
        user_id = session.get('user_id')
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

        # Persist pathway for logged-in users
        if user_id:
            try:
                pathway_model = LearningPathway(
                    id=enriched_pathway.get('id', str(uuid.uuid4())),
                    user_id=user_id,
                    title=enriched_pathway.get('title', 'Learning Pathway'),
                    description=enriched_pathway.get('description', ''),
                    curriculum=json.dumps(enriched_pathway)
                )
                db.session.add(pathway_model)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"DB save pathway error: {e}")
        
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
@api_login_required
def update_pathway_progress(pathway_id):
    """Update progress on a specific resource for a pathway"""
    data = request.json
    # Implementation for progress tracking
    return jsonify({'success': True})

@app.route('/api/adapt-pathway', methods=['POST'])
@api_login_required
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
@login_required
def dashboard():
    """User dashboard showing all pathways and progress"""
    user_id = session.get('user_id')
    if user_id:
        # Attempt to load latest pathway from DB
        latest_pathway = LearningPathway.query.filter_by(user_id=user_id).order_by(LearningPathway.created_at.desc()).first()
        if latest_pathway:
            try:
                session['current_pathway'] = json.loads(latest_pathway.curriculum)
            except Exception:
                pass
    # Calculate real progress data
    dashboard_data = calculate_dashboard_stats()
    return render_template('dashboard.html', **dashboard_data)

def get_db_progress_summary(user_id: str, pathway_id: str | None = None) -> dict:
    """Aggregate user's progress from the database for the specified pathway or latest one."""
    try:
        if not user_id:
            return {}
        # Determine pathway to use
        pathway: LearningPathway | None = None
        if pathway_id:
            pathway = LearningPathway.query.filter_by(id=pathway_id, user_id=user_id).first()
        if not pathway:
            pathway = (
                LearningPathway.query.filter_by(user_id=user_id)
                .order_by(LearningPathway.created_at.desc())
                .first()
            )
        if not pathway:
            return {}
        # Aggregate progress entries for this pathway
        entries = Progress.query.filter_by(user_id=user_id, pathway_id=pathway.id).all()
        completed_resources = [e.resource_id for e in entries if (e.status or '').lower() == 'completed']
        total_time_spent = sum(int(e.time_spent or 0) for e in entries)
        # Derive total resources from curriculum if available
        try:
            curriculum = json.loads(pathway.curriculum) if pathway.curriculum else {}
        except Exception:
            curriculum = {}
        total_resources = 0
        if curriculum:
            for module in curriculum.get('modules', []) or []:
                for topic in module.get('topics', []) or []:
                    total_resources += len(topic.get('resources', []) or [])
        return {
            'pathway_id': pathway.id,
            'completed_resources': completed_resources,
            'time_spent': total_time_spent,
            'pathways_created': LearningPathway.query.filter_by(user_id=user_id).count(),
            'total_resources': total_resources,
        }
    except Exception as e:
        print(f"DB progress summary error: {e}")
        return {}

def calculate_dashboard_stats():
    """Calculate real user progress statistics"""
    # Get current pathway and learning profile
    current_pathway = session.get('current_pathway', None)
    learning_profile = session.get('learning_profile', None)

    # If logged in, hydrate from DB
    user_id = session.get('user_id')
    db_progress = None
    if user_id:
        summary = get_db_progress_summary(user_id, (current_pathway or {}).get('id'))
        if summary:
            db_progress = {
                'completed_resources': summary.get('completed_resources', []),
                'time_spent': summary.get('time_spent', 0),
                'pathways_created': summary.get('pathways_created', 0),
                'skills_progress': {},
            }
            # Ensure current_pathway in session aligns with DB latest
            if not current_pathway or current_pathway.get('id') != summary.get('pathway_id'):
                latest_db = (
                    LearningPathway.query.filter_by(user_id=user_id)
                    .order_by(LearningPathway.created_at.desc())
                    .first()
                )
                if latest_db:
                    try:
                        session['current_pathway'] = json.loads(latest_db.curriculum)
                        current_pathway = session['current_pathway']
                    except Exception:
                        pass

    user_progress = db_progress or session.get('user_progress', {
        'completed_resources': [],
        'time_spent': 0,
        'pathways_created': 0,
        'skills_progress': {}
    })
    
    # Convert time from minutes to hours and round to 1 decimal
    time_spent_hours = round(user_progress.get('time_spent', 0) / 60, 1)
    
    # Initialize stats
    stats = {
        'active_pathways': 0,
        'completed_modules': 0,
        'completed_resources': 0,
        'total_resources': 0,
        'time_spent': time_spent_hours,
        'skills_mastered': 0,
        'recent_activity': [],
        'pathway_data': None,
        'learning_profile': learning_profile,
        'completion_percentage': 0
    }
    
    # Initialize skill progress map
    skill_to_total = {}
    skill_to_completed = {}
    
    if current_pathway:
        stats['active_pathways'] = 1
        stats['pathway_data'] = current_pathway
        
        # Calculate module and resource statistics
        completed_modules = 0
        total_modules = len(current_pathway.get('modules', []))
        total_resources = 0
        completed_resources_count = 0
        completed_resource_ids = set(user_progress.get('completed_resources', []))
        
        # Debug logging
        print(f"DEBUG: Completed resources (aggregated): {completed_resource_ids}")
        print(f"DEBUG: Total modules: {total_modules}")
        
        for module in current_pathway.get('modules', []):
            module_resources = 0
            module_completed_resources = 0
            
            for topic in module.get('topics', []):
                topic_resources = topic.get('resources', [])
                module_resources += len(topic_resources)
                total_resources += len(topic_resources)
                
                # Count per-skill totals
                for skill in (topic.get('skills_gained') or []):
                    skill_to_total[skill] = skill_to_total.get(skill, 0) + len(topic_resources)
                
                for resource in topic_resources:
                    if resource.get('id') in completed_resource_ids:
                        module_completed_resources += 1
                        completed_resources_count += 1
                        for skill in (topic.get('skills_gained') or []):
                            skill_to_completed[skill] = skill_to_completed.get(skill, 0) + 1
            
            # Consider module completed if 80% of resources are done
            if module_resources > 0 and (module_completed_resources / module_resources) >= 0.8:
                completed_modules += 1
                print(f"DEBUG: Module '{module.get('name')}' completed: {module_completed_resources}/{module_resources}")
        
        stats['completed_modules'] = completed_modules
        stats['completed_resources'] = completed_resources_count
        stats['total_resources'] = total_resources
        
        # Calculate overall completion percentage
        if total_resources > 0:
            stats['completion_percentage'] = round((completed_resources_count / total_resources) * 100)
        
        # Calculate skills mastered and per-skill progress
        skills_covered = current_pathway.get('skills_covered', [])
        if total_modules > 0:
            skills_completion_ratio = completed_modules / total_modules
            stats['skills_mastered'] = round(len(skills_covered) * skills_completion_ratio)
        
        # Build simplified per-skill progress for dashboard
        simplified_skills_progress = {}
        for skill, total in skill_to_total.items():
            completed_for_skill = skill_to_completed.get(skill, 0)
            if total > 0:
                simplified_skills_progress[skill] = round((completed_for_skill / total) * 100)
        stats['skills_progress'] = simplified_skills_progress
        
        # Generate recent activity
        stats['recent_activity'] = generate_recent_activity(current_pathway, user_progress)
        
        # Debug final stats
        print(f"DEBUG: Final stats - Completed: {completed_resources_count}, Total: {total_resources}, Time: {time_spent_hours}h")
    
    # Add pathway creation count
    if learning_profile:
        stats['pathways_created'] = user_progress.get('pathways_created', 1)
    
    return stats

def generate_recent_activity(pathway, user_progress):
    """Generate recent activity feed"""
    activities = []
    completed_count = len(user_progress.get('completed_resources', []))
    
    # Add pathway creation activity
    if pathway:
        activities.append({
            'type': 'pathway_created',
            'title': f'Created learning pathway: {pathway.get("title", "Learning Journey")}',
            'description': f'Generated for {pathway.get("target_role", "skill development")}',
            'icon': 'fas fa-route',
            'color': 'primary',
            'time': 'Recently'
        })
    
    # Add resource completion activities (only if there are completed resources)
    if completed_count > 0:
        activities.append({
            'type': 'resources_completed',
            'title': f'Completed {completed_count} learning resource{"s" if completed_count != 1 else ""}',
            'description': 'Keep up the great momentum!',
            'icon': 'fas fa-check-circle',
            'color': 'success',
            'time': 'This session'
        })
        
        # Add time spent activity if significant
        time_spent_minutes = user_progress.get('time_spent', 0)
        if time_spent_minutes > 30:  # More than 30 minutes
            time_spent_hours = round(time_spent_minutes / 60, 1)
            activities.append({
                'type': 'time_spent',
                'title': f'Spent {time_spent_hours} hours learning',
                'description': 'Excellent dedication to your learning goals!',
                'icon': 'fas fa-clock',
                'color': 'info',
                'time': 'This session'
            })
    
    # Add skills learning activity
    skills = pathway.get('skills_covered', []) if pathway else []
    if skills:
        activities.append({
            'type': 'skills_learning',
            'title': f'Learning {len(skills)} key skills',
            'description': ', '.join(skills[:3]) + ('...' if len(skills) > 3 else ''),
            'icon': 'fas fa-cogs',
            'color': 'info',
            'time': 'In progress'
        })
    
    # If no meaningful activity, show default message
    if completed_count == 0:
        activities.append({
            'type': 'getting_started',
            'title': 'Ready to start learning!',
            'description': 'Begin your learning journey by completing resources in your pathway.',
            'icon': 'fas fa-play',
            'color': 'primary',
            'time': 'Now'
        })
    
    return activities[:5]  # Return top 5 activities

# API endpoint to update progress
@app.route('/api/update-progress', methods=['POST'])
@api_login_required
def update_progress():
    """Update user progress"""
    try:
        user_id = session.get('user_id')
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        resource_id = data.get('resource_id')
        action = data.get('action', 'complete')  # complete, uncomplete
        time_spent = data.get('time_spent', 0)
        
        # Get current progress (session fallback)
        user_progress = session.get('user_progress', {
            'completed_resources': [],
            'time_spent': 0,
            'pathways_created': 0,
            'skills_progress': {}
        })
        
        print(f"DEBUG: Before update - Progress: {user_progress}")
        print(f"DEBUG: Resource ID: {resource_id}, Action: {action}, Time: {time_spent}")
        
        if action == 'complete' and resource_id not in user_progress['completed_resources']:
            user_progress['completed_resources'].append(resource_id)
            print(f"DEBUG: Added resource {resource_id} to completed list")
        elif action == 'uncomplete' and resource_id in user_progress['completed_resources']:
            user_progress['completed_resources'].remove(resource_id)
            print(f"DEBUG: Removed resource {resource_id} from completed list")
        
        # Add time spent
        user_progress['time_spent'] += time_spent
        
        # Update session and mark as modified
        session['user_progress'] = user_progress
        session.modified = True

        # Persist progress for logged-in users (upsert by resource)
        if user_id:
            try:
                latest_pathway = (
                    LearningPathway.query.filter_by(user_id=user_id)
                    .order_by(LearningPathway.created_at.desc())
                    .first()
                )
                if latest_pathway and resource_id:
                    entry = Progress.query.filter_by(
                        user_id=user_id,
                        pathway_id=latest_pathway.id,
                        resource_id=resource_id,
                    ).first()
                    if not entry:
                        entry = Progress(
                            user_id=user_id,
                            pathway_id=latest_pathway.id,
                            resource_id=resource_id,
                        )
                        db.session.add(entry)
                    # Update fields
                    if action == 'complete':
                        entry.status = 'completed'
                        entry.completion_percentage = 100.0
                    elif action == 'uncomplete':
                        entry.status = 'not_started'
                        entry.completion_percentage = 0.0
                    # Accumulate time if provided
                    try:
                        entry.time_spent = int(entry.time_spent or 0) + int(time_spent or 0)
                    except Exception:
                        entry.time_spent = int(time_spent or 0)
                    entry.updated_at = datetime.utcnow()
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"DB save progress error: {e}")
        
        print(f"DEBUG: After update - Progress: {user_progress}")
        
        return jsonify({'success': True, 'progress': user_progress})
        
    except Exception as e:
        print(f"Update progress error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-progress', methods=['GET'])
@api_login_required
def get_progress():
    """Get current user progress"""
    try:
        user_id = session.get('user_id')
        pathway_id = request.args.get('pathway_id')
        if user_id:
            summary = get_db_progress_summary(user_id, pathway_id)
            if summary:
                # Also refresh session snapshot to keep UI in sync
                session['user_progress'] = {
                    'completed_resources': summary.get('completed_resources', []),
                    'time_spent': summary.get('time_spent', 0),
                    'pathways_created': summary.get('pathways_created', 0),
                    'skills_progress': {},
                }
                session.modified = True
                return jsonify({'success': True, 'progress': session['user_progress']})
        # Fallback to session-only
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

@app.route('/api/clear-progress', methods=['POST'])
@api_login_required
def clear_progress():
    """Clear all user progress (for testing)"""
    try:
        session['user_progress'] = {
            'completed_resources': [],
            'time_spent': 0,
            'pathways_created': 0,
            'skills_progress': {}
        }
        session.modified = True
        print("DEBUG: Cleared all user progress")
        return jsonify({'success': True, 'message': 'Progress cleared'})
        
    except Exception as e:
        print(f"Clear progress error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/pathway/<pathway_id>')
@login_required
def pathway_view(pathway_id):
    """Detailed view of a specific learning pathway"""
    user_id = session.get('user_id')
    pathway_data = session.get('current_pathway', None)

    # If logged in, try to load that specific pathway from DB
    if user_id:
        db_pathway = LearningPathway.query.filter_by(id=pathway_id, user_id=user_id).first()
        if db_pathway:
            try:
                pathway_data = json.loads(db_pathway.curriculum)
            except Exception:
                pass
    
    # Fallback
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