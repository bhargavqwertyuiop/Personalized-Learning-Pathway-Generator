import requests
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from urllib.parse import quote, urlencode
import time
from datetime import datetime

@dataclass
class Resource:
    id: str
    title: str
    description: str
    url: str
    platform: str
    type: str  # video, article, course, interactive, book, podcast
    duration: Optional[int] = None  # minutes
    difficulty: str = "intermediate"  # beginner, intermediate, advanced
    rating: Optional[float] = None
    enrollment_count: Optional[int] = None
    tags: List[str] = None
    language: str = "en"
    last_updated: Optional[str] = None
    instructor: Optional[str] = None
    thumbnail: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class ResourceAggregator:
    """
    Aggregates free educational resources from multiple platforms:
    - YouTube (videos, playlists, channels)
    - Coursera (free courses and audit options)
    - edX (free courses)
    - Khan Academy (structured lessons)
    - MIT OpenCourseWare
    - Codecademy (free content)
    - freeCodeCamp
    - GitHub repositories and tutorials
    - Academic papers and articles
    - Podcasts
    """
    
    def __init__(self):
        self.platforms = {
            'youtube': YouTubeAggregator(),
            'coursera': CourseraAggregator(),
            'edx': EdXAggregator(),
            'khan_academy': KhanAcademyAggregator(),
            'mit_ocw': MITOpenCourseWareAggregator(),
            'freecodecamp': FreeCodeCampAggregator(),
            'github': GitHubAggregator(),
            'medium': MediumAggregator(),
            'podcast': PodcastAggregator()
        }
        
        # Skill-to-keyword mapping for better search targeting
        self.skill_keywords = {
            'programming': ['programming', 'coding', 'software development', 'computer science'],
            'python': ['python programming', 'python tutorial', 'python course'],
            'javascript': ['javascript', 'js programming', 'web development'],
            'data_analysis': ['data analysis', 'pandas', 'data science', 'statistics'],
            'machine_learning': ['machine learning', 'ML', 'artificial intelligence', 'deep learning'],
            'web_development': ['web development', 'frontend', 'backend', 'full stack'],
            'algorithms': ['algorithms', 'data structures', 'computer science fundamentals'],
            'databases': ['database', 'SQL', 'NoSQL', 'data modeling'],
            'system_design': ['system design', 'architecture', 'scalability', 'distributed systems'],
            'cybersecurity': ['cybersecurity', 'information security', 'ethical hacking', 'network security']
        }
    
    def enrich_pathway(self, pathway: Dict) -> Dict:
        """Enrich a learning pathway with curated resources"""
        enriched_pathway = pathway.copy()
        
        if 'modules' in pathway:
            for module in enriched_pathway['modules']:
                if 'topics' in module:
                    for topic in module['topics']:
                        topic_name = topic.get('name', '')
                        difficulty = topic.get('difficulty', 'intermediate')
                        
                        # Aggregate resources for this topic
                        resources = self.find_resources(topic_name, difficulty, limit=10)
                        topic['resources'] = [asdict(resource) for resource in resources]
        
        return enriched_pathway
    
    def find_resources(self, topic: str, difficulty: str = 'intermediate', 
                      content_types: List[str] = None, limit: int = 20) -> List[Resource]:
        """Find resources for a specific topic across all platforms"""
        if content_types is None:
            content_types = ['video', 'course', 'article', 'interactive']
        
        all_resources = []
        
        # Expand topic with related keywords
        search_terms = self._expand_search_terms(topic)
        
        for platform_name, platform in self.platforms.items():
            try:
                for search_term in search_terms[:3]:  # Limit to prevent too many API calls
                    resources = platform.search_resources(search_term, difficulty, content_types, limit//len(search_terms))
                    all_resources.extend(resources)
                    time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"Error fetching from {platform_name}: {e}")
                continue
        
        # Deduplicate and rank resources
        unique_resources = self._deduplicate_resources(all_resources)
        ranked_resources = self._rank_resources(unique_resources, topic, difficulty)
        
        return ranked_resources[:limit]
    
    def _expand_search_terms(self, topic: str) -> List[str]:
        """Expand topic into related search terms"""
        terms = [topic]
        
        # Add specific keywords for known skills
        topic_lower = topic.lower()
        for skill, keywords in self.skill_keywords.items():
            if skill in topic_lower or any(keyword in topic_lower for keyword in keywords):
                terms.extend(keywords[:2])  # Add top 2 related keywords
                break
        
        return list(set(terms))  # Remove duplicates
    
    def _deduplicate_resources(self, resources: List[Resource]) -> List[Resource]:
        """Remove duplicate resources based on title and URL similarity"""
        unique_resources = []
        seen_titles = set()
        seen_urls = set()
        
        for resource in resources:
            # Normalize title for comparison
            normalized_title = re.sub(r'[^\w\s]', '', resource.title.lower())
            
            if (normalized_title not in seen_titles and 
                resource.url not in seen_urls and
                len(resource.title) > 10):  # Filter out very short titles
                
                unique_resources.append(resource)
                seen_titles.add(normalized_title)
                seen_urls.add(resource.url)
        
        return unique_resources
    
    def _rank_resources(self, resources: List[Resource], topic: str, difficulty: str) -> List[Resource]:
        """Rank resources based on relevance, quality, and user preferences"""
        def calculate_score(resource: Resource) -> float:
            score = 0.0
            
            # Title relevance
            topic_words = topic.lower().split()
            title_words = resource.title.lower().split()
            title_relevance = len(set(topic_words) & set(title_words)) / len(topic_words)
            score += title_relevance * 30
            
            # Difficulty match
            if resource.difficulty == difficulty:
                score += 20
            elif (difficulty == 'beginner' and resource.difficulty == 'intermediate') or \
                 (difficulty == 'advanced' and resource.difficulty == 'intermediate'):
                score += 10
            
            # Platform reliability (based on general quality)
            platform_scores = {
                'youtube': 15, 'coursera': 25, 'edx': 25, 'khan_academy': 20,
                'mit_ocw': 30, 'freecodecamp': 20, 'github': 10, 'medium': 10
            }
            score += platform_scores.get(resource.platform, 5)
            
            # Rating and popularity
            if resource.rating:
                score += (resource.rating / 5.0) * 15
            if resource.enrollment_count:
                score += min(resource.enrollment_count / 10000, 10)  # Cap at 10 points
            
            # Content type preferences
            type_preferences = {'course': 1.2, 'video': 1.1, 'interactive': 1.15, 'article': 1.0}
            score *= type_preferences.get(resource.type, 1.0)
            
            return score
        
        # Sort by calculated score
        resources.sort(key=calculate_score, reverse=True)
        return resources

# Platform-specific aggregators
class YouTubeAggregator:
    """Aggregate educational content from YouTube"""
    
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        # Mock implementation - in production, would use YouTube Data API
        resources = []
        
        # Simulate API call with mock data
        mock_videos = [
            {
                'title': f"Complete {query} Tutorial for Beginners",
                'url': f"https://youtube.com/watch?v=example1",
                'duration': 3600,  # 1 hour
                'rating': 4.5,
                'views': 500000,
                'channel': 'Tech Education'
            },
            {
                'title': f"Advanced {query} Concepts Explained",
                'url': f"https://youtube.com/watch?v=example2", 
                'duration': 2400,  # 40 minutes
                'rating': 4.7,
                'views': 200000,
                'channel': 'Programming Guru'
            }
        ]
        
        for i, video in enumerate(mock_videos[:limit]):
            resource = Resource(
                id=f"yt_{i}_{hash(query)}",
                title=video['title'],
                description=f"Comprehensive {query} tutorial covering key concepts",
                url=video['url'],
                platform='youtube',
                type='video',
                duration=video['duration'] // 60,  # Convert to minutes
                difficulty=self._infer_difficulty(video['title'], difficulty),
                rating=video['rating'],
                enrollment_count=video['views'],
                instructor=video['channel'],
                tags=[query, 'tutorial', 'programming']
            )
            resources.append(resource)
        
        return resources
    
    def _infer_difficulty(self, title: str, default: str) -> str:
        title_lower = title.lower()
        if 'beginner' in title_lower or 'basics' in title_lower or 'intro' in title_lower:
            return 'beginner'
        elif 'advanced' in title_lower or 'expert' in title_lower or 'master' in title_lower:
            return 'advanced'
        return default

class CourseraAggregator:
    """Aggregate free and audit courses from Coursera"""
    
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        resources = []
        
        # Mock Coursera courses
        mock_courses = [
            {
                'title': f"Introduction to {query}",
                'url': f"https://coursera.org/learn/{query.replace(' ', '-').lower()}",
                'instructor': "University Professor",
                'rating': 4.6,
                'enrollments': 50000,
                'duration_weeks': 6
            }
        ]
        
        for i, course in enumerate(mock_courses[:limit]):
            resource = Resource(
                id=f"coursera_{i}_{hash(query)}",
                title=course['title'],
                description=f"University-level course on {query}",
                url=course['url'],
                platform='coursera',
                type='course',
                duration=course['duration_weeks'] * 7 * 60,  # Estimate hours
                difficulty=difficulty,
                rating=course['rating'],
                enrollment_count=course['enrollments'],
                instructor=course['instructor'],
                tags=[query, 'university', 'certification']
            )
            resources.append(resource)
        
        return resources

class EdXAggregator:
    """Aggregate free courses from edX"""
    
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        resources = []
        
        # Mock edX courses
        mock_courses = [
            {
                'title': f"{query} Fundamentals",
                'url': f"https://edx.org/course/{query.replace(' ', '-').lower()}",
                'institution': "MIT",
                'rating': 4.4,
                'enrollments': 30000
            }
        ]
        
        for i, course in enumerate(mock_courses[:limit]):
            resource = Resource(
                id=f"edx_{i}_{hash(query)}",
                title=course['title'],
                description=f"Free course on {query} from {course['institution']}",
                url=course['url'],
                platform='edx',
                type='course',
                difficulty=difficulty,
                rating=course['rating'],
                enrollment_count=course['enrollments'],
                instructor=course['institution'],
                tags=[query, 'university', 'free']
            )
            resources.append(resource)
        
        return resources

class KhanAcademyAggregator:
    """Aggregate structured lessons from Khan Academy"""
    
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        resources = []
        
        # Khan Academy is particularly good for fundamentals
        if any(term in query.lower() for term in ['math', 'statistics', 'computer science', 'programming']):
            resource = Resource(
                id=f"khan_{hash(query)}",
                title=f"{query} - Khan Academy",
                description=f"Interactive lessons and exercises for {query}",
                url=f"https://khanacademy.org/computing/{query.replace(' ', '-').lower()}",
                platform='khan_academy',
                type='interactive',
                difficulty='beginner',
                rating=4.3,
                tags=[query, 'interactive', 'exercises']
            )
            resources.append(resource)
        
        return resources

class MITOpenCourseWareAggregator:
    """Aggregate courses from MIT OpenCourseWare"""
    
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        resources = []
        
        # MIT OCW for computer science and engineering topics
        if any(term in query.lower() for term in ['computer science', 'programming', 'algorithms', 'ai', 'machine learning']):
            resource = Resource(
                id=f"mit_{hash(query)}",
                title=f"MIT: {query}",
                description=f"MIT course materials for {query}",
                url=f"https://ocw.mit.edu/search/?q={quote(query)}",
                platform='mit_ocw',
                type='course',
                difficulty='advanced',
                rating=4.8,
                instructor="MIT Faculty",
                tags=[query, 'mit', 'academic']
            )
            resources.append(resource)
        
        return resources

class FreeCodeCampAggregator:
    """Aggregate content from freeCodeCamp"""
    
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        resources = []
        
        # freeCodeCamp for web development and programming
        if any(term in query.lower() for term in ['web', 'javascript', 'html', 'css', 'programming', 'coding']):
            resource = Resource(
                id=f"fcc_{hash(query)}",
                title=f"freeCodeCamp: {query}",
                description=f"Learn {query} with hands-on projects",
                url=f"https://freecodecamp.org/learn",
                platform='freecodecamp',
                type='interactive',
                difficulty='beginner',
                rating=4.5,
                tags=[query, 'projects', 'certification']
            )
            resources.append(resource)
        
        return resources

class GitHubAggregator:
    """Aggregate educational repositories and tutorials from GitHub"""
    
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        resources = []
        
        # Mock GitHub repositories
        mock_repos = [
            {
                'name': f"awesome-{query.replace(' ', '-').lower()}",
                'description': f"Curated list of {query} resources",
                'stars': 15000,
                'url': f"https://github.com/awesome/{query.replace(' ', '-').lower()}"
            },
            {
                'name': f"{query.replace(' ', '-').lower()}-tutorial",
                'description': f"Complete {query} tutorial with examples",
                'stars': 8000,
                'url': f"https://github.com/tutorial/{query.replace(' ', '-').lower()}"
            }
        ]
        
        for i, repo in enumerate(mock_repos[:limit]):
            resource = Resource(
                id=f"github_{i}_{hash(query)}",
                title=repo['name'],
                description=repo['description'],
                url=repo['url'],
                platform='github',
                type='article',
                difficulty=difficulty,
                enrollment_count=repo['stars'],
                tags=[query, 'open-source', 'tutorial']
            )
            resources.append(resource)
        
        return resources

class MediumAggregator:
    """Aggregate articles from Medium and other blog platforms"""
    
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        resources = []
        
        # Mock Medium articles
        resource = Resource(
            id=f"medium_{hash(query)}",
            title=f"Deep Dive into {query}",
            description=f"Comprehensive article explaining {query} concepts",
            url=f"https://medium.com/topic/{query.replace(' ', '-').lower()}",
            platform='medium',
            type='article',
            difficulty=difficulty,
            rating=4.2,
            tags=[query, 'article', 'explanation']
        )
        resources.append(resource)
        
        return resources

class PodcastAggregator:
    """Aggregate educational podcasts"""
    
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        resources = []
        
        # Mock podcast episodes
        if 'podcast' in content_types:
            resource = Resource(
                id=f"podcast_{hash(query)}",
                title=f"Tech Talk: {query}",
                description=f"Expert discussion on {query}",
                url=f"https://podcast.example.com/{query.replace(' ', '-').lower()}",
                platform='podcast',
                type='podcast',
                duration=45,  # 45 minutes
                difficulty=difficulty,
                rating=4.1,
                tags=[query, 'discussion', 'experts']
            )
            resources.append(resource)
        
        return resources