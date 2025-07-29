import json
import random
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class Question:
    id: str
    text: str
    type: str  # multiple_choice, scale, ranking, scenario
    options: List[str] = None
    category: str = None
    weight: float = 1.0

class AssessmentEngine:
    """
    Advanced assessment engine that evaluates:
    - Learning styles (VARK, Kolb, Gardner's Multiple Intelligences)
    - Cognitive preferences (Sequential vs. Global, Active vs. Reflective)
    - Knowledge level assessment
    - Career goal alignment
    - Time availability and constraints
    """
    
    def __init__(self):
        self.questions = self._initialize_questions()
        self.learning_style_models = {
            'vark': self._vark_model,
            'kolb': self._kolb_model,
            'gardner': self._gardner_model,
            'felder_silverman': self._felder_silverman_model
        }
    
    def _initialize_questions(self) -> List[Question]:
        """Initialize comprehensive assessment questions"""
        questions = []
        
        # VARK Learning Style Questions
        vark_questions = [
            Question("v1", "When learning something new, you prefer to:", "multiple_choice",
                    ["Read detailed explanations and take notes", "Watch videos or demonstrations", 
                     "Listen to lectures or podcasts", "Practice hands-on activities"], "vark"),
            Question("v2", "When trying to remember information, you find it easier when:", "multiple_choice",
                    ["You can visualize charts, diagrams, or mind maps", "You hear it explained aloud",
                     "You write it down or see it in text", "You can practice or apply it"], "vark"),
            Question("v3", "In a meeting, you prefer to:", "multiple_choice",
                    ["See slides and visual presentations", "Hear verbal explanations",
                     "Read written materials beforehand", "Participate in interactive discussions"], "vark"),
        ]
        
        # Kolb Learning Style Questions
        kolb_questions = [
            Question("k1", "When facing a new challenge, you typically:", "multiple_choice",
                    ["Jump in and learn by doing", "Think through all possibilities first",
                     "Look for established methods and theories", "Experiment with different approaches"], "kolb"),
            Question("k2", "You learn best when:", "multiple_choice",
                    ["You can apply concepts immediately", "You can reflect on experiences",
                     "You understand the underlying theory", "You can experiment freely"], "kolb"),
        ]
        
        # Gardner's Multiple Intelligences
        gardner_questions = [
            Question("g1", "Which activities do you enjoy most?", "ranking",
                    ["Solving math problems", "Writing stories or essays", "Drawing or designing",
                     "Playing music", "Physical activities or sports", "Working with others",
                     "Reflecting on life's big questions", "Observing nature"], "gardner"),
            Question("g2", "When explaining something to others, you tend to:", "multiple_choice",
                    ["Use logical steps and examples", "Tell stories or use analogies",
                     "Draw diagrams or use visuals", "Use rhythm or music",
                     "Use gestures and movement", "Involve group activities",
                     "Connect to deeper meanings", "Use nature metaphors"], "gardner"),
        ]
        
        # Felder-Silverman Model
        fs_questions = [
            Question("fs1", "I understand something better after I:", "multiple_choice",
                    ["Try it out", "Think it through"], "felder_silverman"),
            Question("fs2", "I would rather be considered:", "multiple_choice",
                    ["Realistic", "Innovative"], "felder_silverman"),
            Question("fs3", "When I think about what I did yesterday, I am most likely to get:", "multiple_choice",
                    ["A picture", "Words"], "felder_silverman"),
            Question("fs4", "I tend to:", "multiple_choice",
                    ["Understand details of a subject but may be fuzzy about its overall structure",
                     "Understand the big picture but may lack details"], "felder_silverman"),
        ]
        
        # Knowledge Level Assessment
        knowledge_questions = [
            Question("kl1", "How would you rate your programming experience?", "scale",
                    ["Beginner", "Novice", "Intermediate", "Advanced", "Expert"], "knowledge_level"),
            Question("kl2", "How comfortable are you with data analysis?", "scale",
                    ["Never done it", "Basic understanding", "Some experience",
                     "Quite comfortable", "Expert level"], "knowledge_level"),
            Question("kl3", "Your experience with machine learning:", "scale",
                    ["No experience", "Heard about it", "Some online courses",
                     "Practical projects", "Professional experience"], "knowledge_level"),
        ]
        
        # Time and Commitment Assessment
        time_questions = [
            Question("t1", "How much time can you dedicate to learning per week?", "multiple_choice",
                    ["1-3 hours", "4-7 hours", "8-12 hours", "13-20 hours", "20+ hours"], "time_commitment"),
            Question("t2", "What's your preferred learning session length?", "multiple_choice",
                    ["15-30 minutes", "30-60 minutes", "1-2 hours", "2-4 hours", "4+ hours"], "time_commitment"),
            Question("t3", "How consistent is your learning schedule?", "multiple_choice",
                    ["Very irregular", "Somewhat irregular", "Moderately consistent",
                     "Very consistent", "Extremely structured"], "time_commitment"),
        ]
        
        # Career Goal Assessment
        career_questions = [
            Question("c1", "What's your primary career goal?", "multiple_choice",
                    ["Software Developer", "Data Scientist", "Product Manager", "AI/ML Engineer",
                     "Cybersecurity Specialist", "DevOps Engineer", "UI/UX Designer", "Other"], "career_goals"),
            Question("c2", "In what timeframe do you want to achieve your goal?", "multiple_choice",
                    ["3-6 months", "6-12 months", "1-2 years", "2-3 years", "3+ years"], "career_goals"),
            Question("c3", "What's your motivation for learning?", "multiple_choice",
                    ["Career change", "Skill advancement", "Personal interest",
                     "Academic requirements", "Business needs"], "career_goals"),
        ]
        
        # Scenario-based Questions for Deeper Assessment
        scenario_questions = [
            Question("s1", "You're tasked with learning a new technology for work. Your approach:", "multiple_choice",
                    ["Read documentation thoroughly first", "Find video tutorials",
                     "Jump into a hands-on project", "Find a mentor or join a community"], "learning_approach"),
            Question("s2", "When you get stuck on a problem, you typically:", "multiple_choice",
                    ["Keep trying different approaches", "Take a break and come back later",
                     "Ask for help immediately", "Research similar problems online"], "problem_solving"),
        ]
        
        questions.extend(vark_questions + kolb_questions + gardner_questions + 
                        fs_questions + knowledge_questions + time_questions + 
                        career_questions + scenario_questions)
        
        return questions
    
    def get_initial_questions(self) -> List[Dict]:
        """Get a curated set of questions for initial assessment"""
        # Select key questions from each category
        selected_questions = []
        categories = ['vark', 'kolb', 'gardner', 'felder_silverman', 'knowledge_level', 
                     'time_commitment', 'career_goals', 'learning_approach']
        
        for category in categories:
            category_questions = [q for q in self.questions if q.category == category]
            # Select 2-3 questions per category to keep assessment manageable
            selected_questions.extend(random.sample(category_questions, min(2, len(category_questions))))
        
        return [self._question_to_dict(q) for q in selected_questions]
    
    def _question_to_dict(self, question: Question) -> Dict:
        """Convert Question object to dictionary for JSON serialization"""
        return {
            'id': question.id,
            'text': question.text,
            'type': question.type,
            'options': question.options,
            'category': question.category
        }
    
    def process_assessment(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Process assessment responses and generate comprehensive learning profile"""
        profile = {
            'learning_styles': {},
            'knowledge_levels': {},
            'preferences': {},
            'career_profile': {},
            'recommendations': {}
        }
        
        # Process each learning style model
        for model_name, model_func in self.learning_style_models.items():
            profile['learning_styles'][model_name] = model_func(responses)
        
        # Process knowledge levels
        profile['knowledge_levels'] = self._assess_knowledge_levels(responses)
        
        # Process time and learning preferences
        profile['preferences'] = self._assess_preferences(responses)
        
        # Process career goals
        profile['career_profile'] = self._assess_career_profile(responses)
        
        # Generate recommendations
        profile['recommendations'] = self._generate_recommendations(profile)
        
        return profile
    
    def _vark_model(self, responses: Dict) -> Dict:
        """Process VARK (Visual, Auditory, Reading/Writing, Kinesthetic) learning style"""
        scores = {'visual': 0, 'auditory': 0, 'reading_writing': 0, 'kinesthetic': 0}
        
        vark_mapping = {
            'v1': {'visual': [1], 'auditory': [2], 'reading_writing': [0], 'kinesthetic': [3]},
            'v2': {'visual': [0], 'auditory': [1], 'reading_writing': [2], 'kinesthetic': [3]},
            'v3': {'visual': [0], 'auditory': [1], 'reading_writing': [2], 'kinesthetic': [3]}
        }
        
        for question_id, mapping in vark_mapping.items():
            if question_id in responses:
                choice = responses[question_id]
                for style, indices in mapping.items():
                    if choice in indices:
                        scores[style] += 1
        
        # Normalize scores
        total = sum(scores.values()) or 1
        percentages = {style: (score / total) * 100 for style, score in scores.items()}
        
        # Determine primary and secondary styles
        sorted_styles = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'scores': percentages,
            'primary_style': sorted_styles[0][0],
            'secondary_style': sorted_styles[1][0] if len(sorted_styles) > 1 else None,
            'multimodal': len([s for s in percentages.values() if s > 25]) > 1
        }
    
    def _kolb_model(self, responses: Dict) -> Dict:
        """Process Kolb's Learning Style Model"""
        # Concrete Experience vs Abstract Conceptualization
        # Active Experimentation vs Reflective Observation
        
        scores = {
            'concrete_experience': 0,
            'abstract_conceptualization': 0,
            'active_experimentation': 0,
            'reflective_observation': 0
        }
        
        kolb_mapping = {
            'k1': {'active_experimentation': [0, 3], 'reflective_observation': [1, 2]},
            'k2': {'concrete_experience': [0], 'reflective_observation': [1], 
                   'abstract_conceptualization': [2], 'active_experimentation': [3]}
        }
        
        for question_id, mapping in kolb_mapping.items():
            if question_id in responses:
                choice = responses[question_id]
                for dimension, indices in mapping.items():
                    if choice in indices:
                        scores[dimension] += 1
        
        # Determine learning style
        ce_ac = scores['concrete_experience'] - scores['abstract_conceptualization']
        ae_ro = scores['active_experimentation'] - scores['reflective_observation']
        
        if ce_ac > 0 and ae_ro > 0:
            style = 'accommodating'
        elif ce_ac > 0 and ae_ro < 0:
            style = 'diverging'
        elif ce_ac < 0 and ae_ro > 0:
            style = 'converging'
        else:
            style = 'assimilating'
        
        return {
            'style': style,
            'scores': scores,
            'ce_ac_score': ce_ac,
            'ae_ro_score': ae_ro
        }
    
    def _gardner_model(self, responses: Dict) -> Dict:
        """Process Gardner's Multiple Intelligences"""
        intelligences = [
            'logical_mathematical', 'linguistic', 'spatial', 'musical',
            'bodily_kinesthetic', 'interpersonal', 'intrapersonal', 'naturalistic'
        ]
        
        scores = {intel: 0 for intel in intelligences}
        
        # Process ranking question
        if 'g1' in responses and isinstance(responses['g1'], list):
            ranking = responses['g1']
            for i, choice in enumerate(ranking):
                if choice < len(intelligences):
                    scores[intelligences[choice]] += len(ranking) - i
        
        # Process multiple choice questions
        gardner_mapping = {
            'g2': {
                'logical_mathematical': [0], 'linguistic': [1], 'spatial': [2],
                'musical': [3], 'bodily_kinesthetic': [4], 'interpersonal': [5],
                'intrapersonal': [6], 'naturalistic': [7]
            }
        }
        
        for question_id, mapping in gardner_mapping.items():
            if question_id in responses:
                choice = responses[question_id]
                for intelligence, indices in mapping.items():
                    if choice in indices:
                        scores[intelligence] += 3
        
        # Normalize and identify top intelligences
        total = sum(scores.values()) or 1
        percentages = {intel: (score / total) * 100 for intel, score in scores.items()}
        sorted_intelligences = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'scores': percentages,
            'primary_intelligences': [intel for intel, score in sorted_intelligences[:3]],
            'dominant_intelligence': sorted_intelligences[0][0]
        }
    
    def _felder_silverman_model(self, responses: Dict) -> Dict:
        """Process Felder-Silverman Learning Style Model"""
        dimensions = {
            'active_reflective': 0,    # Positive = Active, Negative = Reflective
            'sensing_intuitive': 0,    # Positive = Sensing, Negative = Intuitive  
            'visual_verbal': 0,        # Positive = Visual, Negative = Verbal
            'sequential_global': 0     # Positive = Sequential, Negative = Global
        }
        
        fs_mapping = {
            'fs1': {'active_reflective': {'active': [0], 'reflective': [1]}},
            'fs2': {'sensing_intuitive': {'sensing': [0], 'intuitive': [1]}},
            'fs3': {'visual_verbal': {'visual': [0], 'verbal': [1]}},
            'fs4': {'sequential_global': {'sequential': [0], 'global': [1]}}
        }
        
        for question_id, mapping in fs_mapping.items():
            if question_id in responses:
                choice = responses[question_id]
                for dimension, styles in mapping.items():
                    if choice in styles['active'] or choice in styles.get('sensing', []) or \
                       choice in styles.get('visual', []) or choice in styles.get('sequential', []):
                        dimensions[dimension] += 1
                    else:
                        dimensions[dimension] -= 1
        
        # Convert to style preferences
        styles = {}
        for dimension, score in dimensions.items():
            if 'active_reflective' in dimension:
                styles['processing'] = 'active' if score > 0 else 'reflective'
            elif 'sensing_intuitive' in dimension:
                styles['perception'] = 'sensing' if score > 0 else 'intuitive'
            elif 'visual_verbal' in dimension:
                styles['input'] = 'visual' if score > 0 else 'verbal'
            elif 'sequential_global' in dimension:
                styles['understanding'] = 'sequential' if score > 0 else 'global'
        
        return {
            'dimensions': dimensions,
            'styles': styles,
            'balance_scores': {k: abs(v) for k, v in dimensions.items()}
        }
    
    def _assess_knowledge_levels(self, responses: Dict) -> Dict:
        """Assess knowledge levels across different domains"""
        knowledge_areas = {
            'programming': 'kl1',
            'data_analysis': 'kl2', 
            'machine_learning': 'kl3'
        }
        
        levels = {}
        for area, question_id in knowledge_areas.items():
            if question_id in responses:
                level_mapping = {0: 'beginner', 1: 'novice', 2: 'intermediate', 
                               3: 'advanced', 4: 'expert'}
                levels[area] = level_mapping.get(responses[question_id], 'beginner')
        
        # Calculate overall experience level
        experience_scores = {'beginner': 0, 'novice': 1, 'intermediate': 2, 'advanced': 3, 'expert': 4}
        if levels:
            avg_score = sum(experience_scores.get(level, 0) for level in levels.values()) / len(levels)
            overall_level = min(experience_scores.keys(), key=lambda x: abs(experience_scores[x] - avg_score))
        else:
            overall_level = 'beginner'
        
        return {
            'areas': levels,
            'overall_level': overall_level,
            'strengths': [area for area, level in levels.items() if level in ['advanced', 'expert']],
            'growth_areas': [area for area, level in levels.items() if level in ['beginner', 'novice']]
        }
    
    def _assess_preferences(self, responses: Dict) -> Dict:
        """Assess time commitment and learning preferences"""
        time_mapping = {
            't1': {0: 2, 1: 5.5, 2: 10, 3: 16.5, 4: 25},  # hours per week
            't2': {0: 22.5, 1: 45, 2: 90, 3: 180, 4: 300},  # minutes per session
            't3': {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}  # consistency score
        }
        
        preferences = {}
        
        if 't1' in responses:
            preferences['weekly_hours'] = time_mapping['t1'].get(responses['t1'], 5)
        if 't2' in responses:
            preferences['session_length'] = time_mapping['t2'].get(responses['t2'], 45)
        if 't3' in responses:
            preferences['consistency'] = time_mapping['t3'].get(responses['t3'], 3)
        
        # Learning approach preferences
        approach_mapping = {
            's1': {0: 'documentation_first', 1: 'video_based', 2: 'hands_on', 3: 'community_driven'},
            's2': {0: 'persistent', 1: 'reflective', 2: 'collaborative', 3: 'research_oriented'}
        }
        
        for question_id, mapping in approach_mapping.items():
            if question_id in responses:
                key = f"{question_id}_approach"
                preferences[key] = mapping.get(responses[question_id], 'balanced')
        
        return preferences
    
    def _assess_career_profile(self, responses: Dict) -> Dict:
        """Assess career goals and motivations"""
        career_mapping = {
            'c1': ['Software Developer', 'Data Scientist', 'Product Manager', 'AI/ML Engineer',
                   'Cybersecurity Specialist', 'DevOps Engineer', 'UI/UX Designer', 'Other'],
            'c2': ['3-6 months', '6-12 months', '1-2 years', '2-3 years', '3+ years'],
            'c3': ['Career change', 'Skill advancement', 'Personal interest', 
                   'Academic requirements', 'Business needs']
        }
        
        profile = {}
        
        if 'c1' in responses and responses['c1'] < len(career_mapping['c1']):
            profile['target_role'] = career_mapping['c1'][responses['c1']]
        if 'c2' in responses and responses['c2'] < len(career_mapping['c2']):
            profile['timeline'] = career_mapping['c2'][responses['c2']]
        if 'c3' in responses and responses['c3'] < len(career_mapping['c3']):
            profile['motivation'] = career_mapping['c3'][responses['c3']]
        
        return profile
    
    def _generate_recommendations(self, profile: Dict) -> Dict:
        """Generate learning recommendations based on the complete profile"""
        recommendations = {
            'content_types': [],
            'learning_strategies': [],
            'pacing': {},
            'focus_areas': []
        }
        
        # Content type recommendations based on learning styles
        vark = profile['learning_styles'].get('vark', {})
        primary_style = vark.get('primary_style', 'visual')
        
        content_mapping = {
            'visual': ['infographics', 'diagrams', 'flowcharts', 'video_demos', 'interactive_visualizations'],
            'auditory': ['podcasts', 'video_lectures', 'discussion_forums', 'verbal_explanations'],
            'reading_writing': ['articles', 'documentation', 'written_tutorials', 'note_taking_exercises'],
            'kinesthetic': ['hands_on_projects', 'coding_exercises', 'simulations', 'lab_work']
        }
        
        recommendations['content_types'] = content_mapping.get(primary_style, content_mapping['visual'])
        
        # Learning strategies based on Kolb and Felder-Silverman
        kolb_style = profile['learning_styles'].get('kolb', {}).get('style', 'assimilating')
        strategy_mapping = {
            'accommodating': ['trial_and_error', 'real_world_projects', 'peer_collaboration'],
            'diverging': ['brainstorming', 'case_studies', 'group_discussions'],
            'converging': ['practical_applications', 'problem_solving', 'focused_practice'],
            'assimilating': ['theoretical_understanding', 'logical_progression', 'comprehensive_research']
        }
        
        recommendations['learning_strategies'] = strategy_mapping.get(kolb_style, strategy_mapping['assimilating'])
        
        # Pacing recommendations
        preferences = profile.get('preferences', {})
        recommendations['pacing'] = {
            'weekly_commitment': preferences.get('weekly_hours', 5),
            'session_duration': preferences.get('session_length', 45),
            'intensity': 'moderate' if preferences.get('consistency', 3) >= 3 else 'flexible'
        }
        
        # Focus areas based on career goals and knowledge gaps
        knowledge = profile.get('knowledge_levels', {})
        career = profile.get('career_profile', {})
        
        target_role = career.get('target_role', 'Software Developer')
        role_skills = {
            'Software Developer': ['programming', 'algorithms', 'system_design', 'testing'],
            'Data Scientist': ['statistics', 'machine_learning', 'data_analysis', 'programming'],
            'AI/ML Engineer': ['machine_learning', 'deep_learning', 'programming', 'mathematics'],
            'Product Manager': ['business_analysis', 'user_research', 'project_management', 'data_analysis']
        }
        
        required_skills = role_skills.get(target_role, role_skills['Software Developer'])
        growth_areas = knowledge.get('growth_areas', [])
        
        recommendations['focus_areas'] = [skill for skill in required_skills if skill in growth_areas or True]
        
        return recommendations