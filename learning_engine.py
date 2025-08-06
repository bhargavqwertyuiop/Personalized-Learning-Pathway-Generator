import json
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

@dataclass
class Topic:
    id: str
    name: str
    description: str
    difficulty: str
    estimated_hours: float
    prerequisites: List[str] = None
    skills_gained: List[str] = None
    priority: float = 1.0
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []
        if self.skills_gained is None:
            self.skills_gained = []

@dataclass
class Module:
    id: str
    name: str
    description: str
    topics: List[Topic]
    estimated_weeks: int
    difficulty: str = "intermediate"
    module_type: str = "core"  # core, supplementary, project, assessment

@dataclass
class LearningPathway:
    id: str
    title: str
    description: str
    modules: List[Module]
    total_duration_weeks: int
    difficulty_progression: List[str]
    target_role: str
    skills_covered: List[str]
    learning_objectives: List[str]
    adaptation_metadata: Dict = None
    
    def __post_init__(self):
        if self.adaptation_metadata is None:
            self.adaptation_metadata = {}

class LearningPathwayEngine:
    """
    Advanced learning pathway engine that:
    - Generates personalized curricula based on multiple factors
    - Creates skill dependency graphs
    - Implements adaptive learning algorithms
    - Optimizes learning sequences
    - Provides dynamic difficulty adjustment
    - Tracks learning velocity and adapts pacing
    """
    
    def __init__(self):
        # Knowledge graphs and skill dependencies
        self.skill_dependencies = self._build_skill_dependency_graph()
        self.career_skill_maps = self._build_career_skill_maps()
        self.difficulty_progressions = self._build_difficulty_progressions()
        
        # Learning optimization parameters
        self.optimal_session_lengths = {'beginner': 45, 'intermediate': 60, 'advanced': 90}
        self.retention_curves = self._initialize_retention_models()
        
    def generate_pathway(self, learning_profile: Dict, career_goals: List[str], 
                        timeline: str, focus_areas: List[str]) -> Dict:
        """Generate a comprehensive, personalized learning pathway"""
        
        # Extract key profile information
        learning_style = learning_profile.get('learning_styles', {})
        knowledge_levels = learning_profile.get('knowledge_levels', {})
        preferences = learning_profile.get('preferences', {})
        recommendations = learning_profile.get('recommendations', {})
        
        # Determine target skills and competencies
        target_skills = self._identify_target_skills(career_goals, focus_areas, knowledge_levels)
        
        # Create skill progression plan
        skill_progression = self._plan_skill_progression(target_skills, knowledge_levels, timeline)
        
        # Generate modules and topics
        modules = self._generate_modules(skill_progression, learning_style, preferences)
        
        # Optimize learning sequence
        optimized_modules = self._optimize_learning_sequence(modules, learning_profile)
        
        # Calculate timeline and pacing
        timeline_info = self._calculate_timeline(optimized_modules, preferences, timeline)
        
        # Create pathway object
        pathway = LearningPathway(
            id=f"pathway_{hash(str(career_goals) + str(focus_areas))}",
            title=self._generate_pathway_title(career_goals, focus_areas),
            description=self._generate_pathway_description(career_goals, focus_areas, timeline),
            modules=optimized_modules,
            total_duration_weeks=timeline_info['total_weeks'],
            difficulty_progression=timeline_info['difficulty_progression'],
            target_role=career_goals[0] if career_goals else "General Development",
            skills_covered=target_skills,
            learning_objectives=self._generate_learning_objectives(target_skills, career_goals),
            adaptation_metadata={
                'created_at': datetime.now().isoformat(),
                'learning_profile': learning_profile,
                'optimization_version': '1.0'
            }
        )
        
        return asdict(pathway)
    
    def adapt_pathway(self, pathway_id: str, feedback: Dict) -> Dict:
        """Adapt an existing pathway based on user progress and feedback"""
        
        # Analyze performance metrics
        performance_analysis = self._analyze_performance(feedback)
        
        # Identify adaptation needs
        adaptation_needs = self._identify_adaptation_needs(performance_analysis)
        
        # Apply adaptations
        adapted_pathway = self._apply_adaptations(pathway_id, adaptation_needs, feedback)
        
        return adapted_pathway
    
    def _build_skill_dependency_graph(self) -> Dict:
        """Build a comprehensive skill dependency graph"""
        return {
            # Programming fundamentals
            'programming_basics': {
                'prerequisites': [],
                'enables': ['python_basics', 'javascript_basics', 'algorithms_basics'],
                'category': 'foundational',
                'difficulty': 'beginner'
            },
            'python_basics': {
                'prerequisites': ['programming_basics'],
                'enables': ['data_analysis', 'web_backend', 'machine_learning'],
                'category': 'language',
                'difficulty': 'beginner'
            },
            'javascript_basics': {
                'prerequisites': ['programming_basics'],
                'enables': ['web_frontend', 'full_stack_development', 'node_js'],
                'category': 'language',
                'difficulty': 'beginner'
            },
            
            # Data Science path
            'statistics': {
                'prerequisites': [],
                'enables': ['data_analysis', 'machine_learning', 'data_visualization'],
                'category': 'mathematics',
                'difficulty': 'intermediate'
            },
            'data_analysis': {
                'prerequisites': ['python_basics', 'statistics'],
                'enables': ['machine_learning', 'data_engineering', 'business_intelligence'],
                'category': 'data_science',
                'difficulty': 'intermediate'
            },
            'machine_learning': {
                'prerequisites': ['data_analysis', 'statistics'],
                'enables': ['deep_learning', 'ai_engineering', 'mlops'],
                'category': 'ai_ml',
                'difficulty': 'advanced'
            },
            'deep_learning': {
                'prerequisites': ['machine_learning'],
                'enables': ['computer_vision', 'nlp', 'generative_ai'],
                'category': 'ai_ml',
                'difficulty': 'advanced'
            },
            
            # Web Development path
            'html_css': {
                'prerequisites': [],
                'enables': ['web_frontend', 'responsive_design', 'ui_design'],
                'category': 'web_frontend',
                'difficulty': 'beginner'
            },
            'web_frontend': {
                'prerequisites': ['html_css', 'javascript_basics'],
                'enables': ['react', 'vue', 'angular', 'full_stack_development'],
                'category': 'web_frontend',
                'difficulty': 'intermediate'
            },
            'web_backend': {
                'prerequisites': ['python_basics'],
                'enables': ['api_development', 'database_design', 'full_stack_development'],
                'category': 'web_backend',
                'difficulty': 'intermediate'
            },
            
            # System Design and Architecture
            'algorithms_basics': {
                'prerequisites': ['programming_basics'],
                'enables': ['data_structures', 'system_design', 'competitive_programming'],
                'category': 'computer_science',
                'difficulty': 'intermediate'
            },
            'data_structures': {
                'prerequisites': ['algorithms_basics'],
                'enables': ['system_design', 'performance_optimization'],
                'category': 'computer_science',
                'difficulty': 'intermediate'
            },
            'system_design': {
                'prerequisites': ['data_structures', 'web_backend'],
                'enables': ['distributed_systems', 'microservices', 'cloud_architecture'],
                'category': 'architecture',
                'difficulty': 'advanced'
            },
            
            # DevOps and Infrastructure
            'linux_basics': {
                'prerequisites': [],
                'enables': ['devops', 'cloud_computing', 'system_administration'],
                'category': 'infrastructure',
                'difficulty': 'beginner'
            },
            'devops': {
                'prerequisites': ['linux_basics', 'web_backend'],
                'enables': ['ci_cd', 'containerization', 'cloud_architecture'],
                'category': 'infrastructure',
                'difficulty': 'advanced'
            },
            
            # Security
            'cybersecurity_basics': {
                'prerequisites': ['programming_basics'],
                'enables': ['ethical_hacking', 'security_architecture', 'incident_response'],
                'category': 'security',
                'difficulty': 'intermediate'
            }
        }
    
    def _build_career_skill_maps(self) -> Dict:
        """Map career roles to required skills"""
        return {
            'Software Developer': {
                'core_skills': ['programming_basics', 'algorithms_basics', 'data_structures'],
                'language_skills': ['python_basics', 'javascript_basics'],
                'specialization_options': ['web_frontend', 'web_backend', 'full_stack_development'],
                'advanced_skills': ['system_design', 'performance_optimization'],
                'soft_skills': ['problem_solving', 'code_review', 'debugging']
            },
            'Data Scientist': {
                'core_skills': ['statistics', 'data_analysis', 'python_basics'],
                'specialization_options': ['machine_learning', 'data_visualization', 'business_intelligence'],
                'advanced_skills': ['deep_learning', 'big_data', 'mlops'],
                'soft_skills': ['business_acumen', 'communication', 'hypothesis_testing']
            },
            'AI/ML Engineer': {
                'core_skills': ['machine_learning', 'python_basics', 'statistics'],
                'specialization_options': ['deep_learning', 'computer_vision', 'nlp'],
                'advanced_skills': ['mlops', 'model_deployment', 'distributed_training'],
                'soft_skills': ['research_methodology', 'experimentation', 'technical_writing']
            },
            'Full Stack Developer': {
                'core_skills': ['programming_basics', 'web_frontend', 'web_backend'],
                'language_skills': ['javascript_basics', 'python_basics'],
                'specialization_options': ['react', 'node_js', 'database_design'],
                'advanced_skills': ['system_design', 'devops', 'performance_optimization'],
                'soft_skills': ['project_management', 'ui_ux_basics', 'api_design']
            },
            'DevOps Engineer': {
                'core_skills': ['linux_basics', 'devops', 'programming_basics'],
                'specialization_options': ['containerization', 'ci_cd', 'cloud_computing'],
                'advanced_skills': ['kubernetes', 'infrastructure_as_code', 'monitoring'],
                'soft_skills': ['automation_mindset', 'troubleshooting', 'collaboration']
            },
            'Cybersecurity Specialist': {
                'core_skills': ['cybersecurity_basics', 'programming_basics', 'linux_basics'],
                'specialization_options': ['ethical_hacking', 'security_architecture', 'incident_response'],
                'advanced_skills': ['malware_analysis', 'cryptography', 'threat_hunting'],
                'soft_skills': ['risk_assessment', 'compliance', 'communication']
            }
        }
    
    def _build_difficulty_progressions(self) -> Dict:
        """Define optimal difficulty progressions for different learning styles"""
        return {
            'gradual': ['beginner', 'beginner', 'intermediate', 'intermediate', 'advanced'],
            'steep': ['beginner', 'intermediate', 'intermediate', 'advanced', 'advanced'],
            'plateau': ['beginner', 'intermediate', 'intermediate', 'intermediate', 'advanced'],
            'mixed': ['beginner', 'intermediate', 'beginner', 'advanced', 'intermediate']
        }
    
    def _initialize_retention_models(self) -> Dict:
        """Initialize learning retention curve models"""
        return {
            'spaced_repetition': {
                'initial_interval': 1,  # days
                'multiplier': 2.5,
                'ease_factor': 2.5
            },
            'forgetting_curve': {
                'retention_rate': 0.8,  # 80% retention after optimal spacing
                'decay_constant': 0.1
            }
        }
    
    def _identify_target_skills(self, career_goals: List[str], focus_areas: List[str], 
                               knowledge_levels: Dict) -> List[str]:
        """Identify target skills based on career goals and current knowledge"""
        target_skills = []
        
        # Get skills for primary career goal
        if career_goals:
            primary_career = career_goals[0]
            career_map = self.career_skill_maps.get(primary_career, {})
            
            # Add core skills
            target_skills.extend(career_map.get('core_skills', []))
            
            # Add language skills if needed
            current_knowledge = knowledge_levels.get('areas', {})
            if current_knowledge.get('programming', 'beginner') in ['beginner', 'novice']:
                target_skills.extend(career_map.get('language_skills', []))
            
            # Add specialization based on focus areas
            specializations = career_map.get('specialization_options', [])
            for focus_area in focus_areas:
                for spec in specializations:
                    if focus_area.lower() in spec.lower():
                        target_skills.append(spec)
        
        # Add focus areas directly
        target_skills.extend(focus_areas)
        
        # Remove duplicates and filter based on prerequisites
        target_skills = list(set(target_skills))
        
        return target_skills
    
    def _plan_skill_progression(self, target_skills: List[str], knowledge_levels: Dict, 
                               timeline: str) -> Dict:
        """Plan the optimal skill learning progression"""
        
        # Calculate available time
        timeline_weeks = self._parse_timeline(timeline)
        
        # Build dependency-ordered skill list
        ordered_skills = self._topological_sort_skills(target_skills)
        
        # Estimate time requirements
        time_estimates = self._estimate_learning_times(ordered_skills, knowledge_levels)
        
        # Create phases based on dependencies and timeline
        phases = self._create_learning_phases(ordered_skills, time_estimates, timeline_weeks)
        
        return {
            'ordered_skills': ordered_skills,
            'time_estimates': time_estimates,
            'phases': phases,
            'total_weeks': timeline_weeks
        }
    
    def _topological_sort_skills(self, skills: List[str]) -> List[str]:
        """Sort skills in dependency order using topological sort"""
        # Build adjacency list
        graph = {}
        in_degree = {}
        
        for skill in skills:
            if skill in self.skill_dependencies:
                graph[skill] = []
                in_degree[skill] = 0
        
        # Add edges and calculate in-degrees
        for skill in skills:
            if skill in self.skill_dependencies:
                prereqs = self.skill_dependencies[skill].get('prerequisites', [])
                for prereq in prereqs:
                    if prereq in graph:
                        graph[prereq].append(skill)
                        in_degree[skill] += 1
        
        # Kahn's algorithm
        queue = [skill for skill in in_degree if in_degree[skill] == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Add any remaining skills not in dependency graph
        for skill in skills:
            if skill not in result:
                result.append(skill)
        
        return result
    
    def _estimate_learning_times(self, skills: List[str], knowledge_levels: Dict) -> Dict:
        """Estimate learning time for each skill based on current knowledge"""
        
        base_times = {
            'beginner': 40,    # hours
            'intermediate': 60,
            'advanced': 80
        }
        
        estimates = {}
        current_knowledge = knowledge_levels.get('areas', {})
        overall_level = knowledge_levels.get('overall_level', 'beginner')
        
        for skill in skills:
            if skill in self.skill_dependencies:
                skill_difficulty = self.skill_dependencies[skill].get('difficulty', 'intermediate')
                base_time = base_times[skill_difficulty]
                
                # Adjust based on current knowledge
                if skill in current_knowledge:
                    current_level = current_knowledge[skill]
                    if current_level in ['advanced', 'expert']:
                        base_time *= 0.3  # Already know this
                    elif current_level == 'intermediate':
                        base_time *= 0.6  # Some knowledge
                    elif current_level == 'novice':
                        base_time *= 0.8  # Basic knowledge
                
                # Adjust based on overall experience
                experience_multipliers = {
                    'beginner': 1.2,
                    'novice': 1.1,
                    'intermediate': 1.0,
                    'advanced': 0.8,
                    'expert': 0.6
                }
                base_time *= experience_multipliers.get(overall_level, 1.0)
                
                estimates[skill] = max(base_time, 10)  # Minimum 10 hours
            else:
                estimates[skill] = 30  # Default for unknown skills
        
        return estimates
    
    def _create_learning_phases(self, skills: List[str], time_estimates: Dict, 
                               total_weeks: int) -> List[Dict]:
        """Create learning phases that fit within the timeline"""
        
        phases = []
        current_phase_skills = []
        current_phase_time = 0
        time_per_phase = (sum(time_estimates.values()) / total_weeks) * 4  # Roughly monthly phases
        
        for skill in skills:
            skill_time = time_estimates.get(skill, 30)
            
            if current_phase_time + skill_time > time_per_phase and current_phase_skills:
                # Create current phase
                phases.append({
                    'skills': current_phase_skills.copy(),
                    'estimated_hours': current_phase_time,
                    'estimated_weeks': math.ceil(current_phase_time / 10)  # Assume 10 hours/week
                })
                
                # Start new phase
                current_phase_skills = [skill]
                current_phase_time = skill_time
            else:
                current_phase_skills.append(skill)
                current_phase_time += skill_time
        
        # Add final phase
        if current_phase_skills:
            phases.append({
                'skills': current_phase_skills,
                'estimated_hours': current_phase_time,
                'estimated_weeks': math.ceil(current_phase_time / 10)
            })
        
        return phases
    
    def _generate_modules(self, skill_progression: Dict, learning_style: Dict, 
                         preferences: Dict) -> List[Module]:
        """Generate learning modules based on skill progression and preferences"""
        
        modules = []
        phases = skill_progression['phases']
        
        for i, phase in enumerate(phases):
            # Create topics for each skill in the phase
            topics = []
            
            for skill in phase['skills']:
                skill_topics = self._generate_skill_topics(skill, learning_style)
                topics.extend(skill_topics)
            
            # Create module
            module = Module(
                id=f"module_{i+1}",
                name=f"Phase {i+1}: {', '.join(phase['skills'][:2])}{'...' if len(phase['skills']) > 2 else ''}",
                description=f"Master {', '.join(phase['skills'])} through hands-on practice and theory",
                topics=topics,
                estimated_weeks=phase['estimated_weeks'],
                difficulty=self._determine_module_difficulty(phase['skills']),
                module_type='core'
            )
            
            modules.append(module)
        
        # Add project modules between core modules
        modules = self._add_project_modules(modules, skill_progression)
        
        return modules
    
    def _generate_skill_topics(self, skill: str, learning_style: Dict) -> List[Topic]:
        """Generate topics for a specific skill"""
        
        # Topic templates based on skill
        topic_templates = {
            'programming_basics': [
                ('Variables and Data Types', 'Learn fundamental programming concepts', 8),
                ('Control Structures', 'Master loops, conditionals, and functions', 12),
                ('Problem Solving', 'Apply programming to solve real problems', 10)
            ],
            'python_basics': [
                ('Python Syntax', 'Learn Python language fundamentals', 8),
                ('Data Structures', 'Work with lists, dictionaries, and sets', 10),
                ('File Handling', 'Read and write files in Python', 6),
                ('Libraries and Modules', 'Use Python standard library', 8)
            ],
            'data_analysis': [
                ('Pandas Fundamentals', 'Data manipulation with Pandas', 12),
                ('Data Visualization', 'Create charts and graphs', 10),
                ('Statistical Analysis', 'Descriptive and inferential statistics', 15),
                ('Real-world Projects', 'Analyze actual datasets', 8)
            ],
            'machine_learning': [
                ('ML Fundamentals', 'Understanding machine learning concepts', 10),
                ('Supervised Learning', 'Classification and regression algorithms', 15),
                ('Unsupervised Learning', 'Clustering and dimensionality reduction', 12),
                ('Model Evaluation', 'Validation and performance metrics', 8),
                ('MLOps Basics', 'Deploying and monitoring ML models', 10)
            ]
        }
        
        templates = topic_templates.get(skill, [
            (f'{skill.title()} Fundamentals', f'Learn the basics of {skill}', 10),
            (f'{skill.title()} Practice', f'Hands-on practice with {skill}', 12),
            (f'{skill.title()} Projects', f'Apply {skill} to real projects', 8)
        ])
        
        topics = []
        for i, (name, description, hours) in enumerate(templates):
            topic = Topic(
                id=f"{skill}_topic_{i+1}",
                name=name,
                description=description,
                difficulty=self.skill_dependencies.get(skill, {}).get('difficulty', 'intermediate'),
                estimated_hours=hours,
                skills_gained=[skill],
                priority=1.0 - (i * 0.1)  # Earlier topics have higher priority
            )
            topics.append(topic)
        
        return topics
    
    def _optimize_learning_sequence(self, modules: List[Module], learning_profile: Dict) -> List[Module]:
        """Optimize the sequence of modules based on learning preferences"""
        
        learning_style = learning_profile.get('learning_styles', {})
        preferences = learning_profile.get('preferences', {})
        
        # Apply learning style optimizations
        vark_style = learning_style.get('vark', {}).get('primary_style', 'visual')
        kolb_style = learning_style.get('kolb', {}).get('style', 'assimilating')
        
        # Reorder modules based on learning preferences
        if kolb_style == 'accommodating':
            # Prefer hands-on, practical modules first
            modules.sort(key=lambda m: (m.module_type != 'project', m.estimated_weeks))
        elif kolb_style == 'assimilating':
            # Prefer theoretical understanding first
            modules.sort(key=lambda m: (m.module_type == 'project', m.estimated_weeks))
        
        # Adjust topic order within modules
        for module in modules:
            module.topics = self._optimize_topic_sequence(module.topics, learning_style)
        
        return modules
    
    def _optimize_topic_sequence(self, topics: List[Topic], learning_style: Dict) -> List[Topic]:
        """Optimize the sequence of topics within a module"""
        
        # Sort by prerequisites first, then by learning style preferences
        vark_style = learning_style.get('vark', {}).get('primary_style', 'visual')
        
        if vark_style == 'kinesthetic':
            # Prefer hands-on topics first
            topics.sort(key=lambda t: (len(t.prerequisites), 'practice' not in t.name.lower()))
        else:
            # Standard prerequisite-based ordering
            topics.sort(key=lambda t: (len(t.prerequisites), -t.priority))
        
        return topics
    
    def _add_project_modules(self, modules: List[Module], skill_progression: Dict) -> List[Module]:
        """Add project modules between core learning modules"""
        
        enhanced_modules = []
        
        for i, module in enumerate(modules):
            enhanced_modules.append(module)
            
            # Add project module after every 2-3 core modules
            if (i + 1) % 2 == 0 and i < len(modules) - 1:
                project_module = self._create_project_module(module, i + 1)
                enhanced_modules.append(project_module)
        
        return enhanced_modules
    
    def _create_project_module(self, previous_module: Module, module_index: int) -> Module:
        """Create a project module that applies skills from previous modules"""
        
        # Gather skills from previous modules
        skills_to_apply = []
        for topic in previous_module.topics:
            skills_to_apply.extend(topic.skills_gained)
        
        # Create project topic
        project_topic = Topic(
            id=f"project_{module_index}",
            name=f"Capstone Project: {previous_module.name}",
            description=f"Apply {', '.join(skills_to_apply[:3])} in a real-world project",
            difficulty=previous_module.difficulty,
            estimated_hours=20,
            prerequisites=skills_to_apply,
            skills_gained=['project_experience', 'portfolio_development'],
            priority=1.0
        )
        
        project_module = Module(
            id=f"project_module_{module_index}",
            name=f"Project Module {module_index}",
            description="Apply your learning through hands-on projects",
            topics=[project_topic],
            estimated_weeks=2,
            difficulty=previous_module.difficulty,
            module_type='project'
        )
        
        return project_module
    
    def _calculate_timeline(self, modules: List[Module], preferences: Dict, 
                           target_timeline: str) -> Dict:
        """Calculate realistic timeline and difficulty progression"""
        
        total_weeks = sum(module.estimated_weeks for module in modules)
        target_weeks = self._parse_timeline(target_timeline)
        
        # Adjust if needed
        if total_weeks > target_weeks:
            # Compress timeline
            compression_factor = target_weeks / total_weeks
            for module in modules:
                module.estimated_weeks = max(1, int(module.estimated_weeks * compression_factor))
            total_weeks = target_weeks
        
        # Create difficulty progression
        difficulty_progression = []
        for module in modules:
            difficulty_progression.extend([module.difficulty] * module.estimated_weeks)
        
        return {
            'total_weeks': total_weeks,
            'difficulty_progression': difficulty_progression,
            'weekly_commitment': preferences.get('weekly_hours', 10),
            'session_length': preferences.get('session_length', 60)
        }
    
    def _parse_timeline(self, timeline: str) -> int:
        """Parse timeline string to weeks"""
        timeline_mapping = {
            '3-6 months': 18,   # Average 4.5 months
            '6-12 months': 39,  # Average 9.75 months  
            '1-2 years': 78,    # Average 1.5 years
            '2-3 years': 130,   # Average 2.5 years
            '3+ years': 156     # 3 years
        }
        return timeline_mapping.get(timeline, 26)  # Default to 6 months
    
    def _determine_module_difficulty(self, skills: List[str]) -> str:
        """Determine module difficulty based on constituent skills"""
        difficulties = []
        for skill in skills:
            if skill in self.skill_dependencies:
                difficulties.append(self.skill_dependencies[skill].get('difficulty', 'intermediate'))
        
        if not difficulties:
            return 'intermediate'
        
        # Return the most common difficulty level
        difficulty_counts = {}
        for diff in difficulties:
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        
        return max(difficulty_counts.items(), key=lambda x: x[1])[0]
    
    def _generate_pathway_title(self, career_goals: List[str], focus_areas: List[str]) -> str:
        """Generate an engaging title for the learning pathway"""
        if career_goals:
            primary_goal = career_goals[0]
            if focus_areas:
                return f"Become a {primary_goal}: {focus_areas[0]} Specialization"
            else:
                return f"Complete {primary_goal} Learning Path"
        elif focus_areas:
            return f"Master {focus_areas[0]}: Comprehensive Guide"
        else:
            return "Personalized Learning Journey"
    
    def _generate_pathway_description(self, career_goals: List[str], focus_areas: List[str], 
                                     timeline: str) -> str:
        """Generate a detailed description for the learning pathway"""
        desc_parts = []
        
        if career_goals:
            desc_parts.append(f"This comprehensive pathway will prepare you for a career as a {career_goals[0]}")
        
        if focus_areas:
            desc_parts.append(f"with specialized focus on {', '.join(focus_areas)}")
        
        desc_parts.append(f"Designed to be completed in {timeline.lower()}")
        desc_parts.append("this adaptive curriculum combines theory, practice, and real-world projects")
        
        return ". ".join(desc_parts) + "."
    
    def _generate_learning_objectives(self, target_skills: List[str], career_goals: List[str]) -> List[str]:
        """Generate specific learning objectives"""
        objectives = []
        
        # Core objectives based on skills
        for skill in target_skills[:5]:  # Top 5 skills
            if skill in self.skill_dependencies:
                skill_name = skill.replace('_', ' ').title()
                objectives.append(f"Master {skill_name} concepts and applications")
        
        # Career-specific objectives
        if career_goals:
            primary_career = career_goals[0]
            career_map = self.career_skill_maps.get(primary_career, {})
            soft_skills = career_map.get('soft_skills', [])
            
            for soft_skill in soft_skills[:2]:  # Top 2 soft skills
                skill_name = soft_skill.replace('_', ' ').title()
                objectives.append(f"Develop {skill_name} abilities")
        
        # General objectives
        objectives.extend([
            "Build a strong portfolio of projects",
            "Gain hands-on experience with industry tools",
            "Develop problem-solving and critical thinking skills"
        ])
        
        return objectives[:6]  # Limit to 6 objectives
    
    def _analyze_performance(self, feedback: Dict) -> Dict:
        """Analyze user performance from feedback data"""
        
        completion_rates = feedback.get('completion_rates', {})
        time_spent = feedback.get('time_spent', {})
        difficulty_ratings = feedback.get('difficulty_ratings', {})
        engagement_scores = feedback.get('engagement_scores', {})
        
        analysis = {
            'overall_progress': sum(completion_rates.values()) / len(completion_rates) if completion_rates else 0,
            'learning_velocity': self._calculate_learning_velocity(time_spent, completion_rates),
            'struggle_areas': self._identify_struggle_areas(completion_rates, difficulty_ratings),
            'engagement_level': sum(engagement_scores.values()) / len(engagement_scores) if engagement_scores else 3,
            'time_efficiency': self._calculate_time_efficiency(time_spent)
        }
        
        return analysis
    
    def _calculate_learning_velocity(self, time_spent: Dict, completion_rates: Dict) -> float:
        """Calculate how quickly the user is learning"""
        if not time_spent or not completion_rates:
            return 1.0
        
        # Calculate average completion rate per hour
        total_time = sum(time_spent.values())
        total_completion = sum(completion_rates.values())
        
        if total_time > 0:
            return total_completion / total_time
        return 1.0
    
    def _identify_struggle_areas(self, completion_rates: Dict, difficulty_ratings: Dict) -> List[str]:
        """Identify areas where the user is struggling"""
        struggle_areas = []
        
        for topic, completion in completion_rates.items():
            difficulty = difficulty_ratings.get(topic, 3)
            
            # If completion is low and difficulty is rated high
            if completion < 0.6 and difficulty > 3:
                struggle_areas.append(topic)
        
        return struggle_areas
    
    def _calculate_time_efficiency(self, time_spent: Dict) -> float:
        """Calculate how efficiently the user is using their time"""
        if not time_spent:
            return 1.0
        
        # Compare actual time spent vs estimated time
        # This is a simplified calculation - in practice would use more sophisticated metrics
        avg_time = sum(time_spent.values()) / len(time_spent)
        expected_avg = 60  # Expected average minutes per topic
        
        return min(expected_avg / avg_time, 2.0) if avg_time > 0 else 1.0
    
    def _identify_adaptation_needs(self, performance_analysis: Dict) -> Dict:
        """Identify what adaptations are needed based on performance"""
        adaptations = {
            'difficulty_adjustment': 'none',
            'pacing_adjustment': 'none',
            'content_type_changes': [],
            'additional_support': [],
            'advanced_challenges': []
        }
        
        # Difficulty adjustments
        if performance_analysis['overall_progress'] < 0.4:
            adaptations['difficulty_adjustment'] = 'decrease'
        elif performance_analysis['overall_progress'] > 0.9:
            adaptations['difficulty_adjustment'] = 'increase'
        
        # Pacing adjustments
        if performance_analysis['learning_velocity'] < 0.5:
            adaptations['pacing_adjustment'] = 'slower'
        elif performance_analysis['learning_velocity'] > 1.5:
            adaptations['pacing_adjustment'] = 'faster'
        
        # Content type changes based on engagement
        if performance_analysis['engagement_level'] < 2.5:
            adaptations['content_type_changes'] = ['more_interactive', 'shorter_sessions', 'gamification']
        
        # Additional support for struggle areas
        if performance_analysis['struggle_areas']:
            adaptations['additional_support'] = ['peer_mentoring', 'extra_practice', 'prerequisite_review']
        
        return adaptations
    
    def _apply_adaptations(self, pathway_id: str, adaptation_needs: Dict, feedback: Dict) -> Dict:
        """Apply the identified adaptations to the pathway"""
        
        # This would modify the existing pathway in practice
        # For now, return a summary of adaptations applied
        
        adaptations_applied = []
        
        if adaptation_needs['difficulty_adjustment'] != 'none':
            adaptations_applied.append(f"Adjusted difficulty: {adaptation_needs['difficulty_adjustment']}")
        
        if adaptation_needs['pacing_adjustment'] != 'none':
            adaptations_applied.append(f"Modified pacing: {adaptation_needs['pacing_adjustment']}")
        
        if adaptation_needs['content_type_changes']:
            adaptations_applied.append(f"Changed content types: {', '.join(adaptation_needs['content_type_changes'])}")
        
        return {
            'pathway_id': pathway_id,
            'adaptations_applied': adaptations_applied,
            'adaptation_timestamp': datetime.now().isoformat(),
            'performance_metrics': feedback,
            'next_review_date': (datetime.now() + timedelta(weeks=2)).isoformat()
        }