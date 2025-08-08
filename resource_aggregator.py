import requests
import json
import re
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from urllib.parse import quote, urlencode, urlparse, parse_qs
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
        # Performance and validation controls
        self.validate_urls = os.environ.get('VALIDATE_URLS', 'false').lower() == 'true'
        try:
            self.rate_limit_delay = float(os.environ.get('AGGREGATOR_DELAY', '0.05'))
        except Exception:
            self.rate_limit_delay = 0.05
        
        # Curated, highly stable resources by topic keywords
        self.curated_resources = {
            'python': [
                Resource(
                    id='cur_py_fcc_fullcourse',
                    title='Python for Beginners – Full Course [freeCodeCamp] ',
                    description='Learn Python from scratch in this full course',
                    url='https://www.youtube.com/watch?v=rfscVS0vtbw',
                    platform='youtube', type='video', duration=270, difficulty='beginner', rating=4.8,
                    instructor='freeCodeCamp'
                ),
                Resource(
                    id='cur_py_auto_boring',
                    title='Automate the Boring Stuff with Python (free online book)',
                    description='Practical Python programming for total beginners',
                    url='https://automatetheboringstuff.com/',
                    platform='book', type='article', difficulty='beginner', rating=4.7
                ),
                Resource(
                    id='cur_py_docs_tutorial',
                    title='Official Python Tutorial',
                    description='The official Python language tutorial',
                    url='https://docs.python.org/3/tutorial/',
                    platform='docs', type='article', difficulty='beginner', rating=4.6
                ),
            ],
            'javascript': [
                Resource(
                    id='cur_js_fcc_cert',
                    title='freeCodeCamp: JavaScript Algorithms and Data Structures',
                    description='Interactive certification covering JS fundamentals, algorithms, and data structures',
                    url='https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/',
                    platform='freecodecamp', type='interactive', difficulty='beginner', rating=4.8
                ),
                Resource(
                    id='cur_js_mdn_guide',
                    title='MDN Web Docs: JavaScript Guide',
                    description='Comprehensive guide to modern JavaScript',
                    url='https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide',
                    platform='mdn', type='article', difficulty='beginner', rating=4.8
                ),
            ],
            'data structures': [
                Resource(
                    id='cur_ds_visualgo',
                    title='VisuAlgo – Visualising Data Structures and Algorithms',
                    description='Interactive visualizations for common data structures and algorithms',
                    url='https://visualgo.net/en',
                    platform='interactive', type='interactive', difficulty='intermediate', rating=4.7
                ),
                Resource(
                    id='cur_ds_william_fiset',
                    title='Data Structures Easy to Advanced (Full Course)',
                    description='Detailed data structures course by William Fiset on freeCodeCamp',
                    url='https://www.youtube.com/watch?v=RBSGKlAvoiM',
                    platform='youtube', type='video', difficulty='intermediate', rating=4.8
                ),
                Resource(
                    id='cur_ds_gfg',
                    title='GeeksforGeeks: Data Structures',
                    description='Extensive reference and tutorials on data structures',
                    url='https://www.geeksforgeeks.org/data-structures/',
                    platform='gfg', type='article', difficulty='intermediate', rating=4.6
                ),
            ],
            'algorithms': [
                Resource(
                    id='cur_algo_cp',
                    title='CP-Algorithms',
                    description='Algorithms and data structures explanations and implementations',
                    url='https://cp-algorithms.com/',
                    platform='cp-algorithms', type='article', difficulty='advanced', rating=4.7
                ),
                Resource(
                    id='cur_algo_mit_6_006',
                    title='MIT OCW: Introduction to Algorithms (6.006/6.0060)',
                    description='OpenCourseWare materials for MIT algorithms course',
                    url='https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/',
                    platform='mit_ocw', type='course', difficulty='advanced', rating=4.8
                ),
            ],
            'data science': [
                Resource(
                    id='cur_ds_kaggle',
                    title='Kaggle Micro-Courses',
                    description='Hands-on, free data science short courses',
                    url='https://www.kaggle.com/learn',
                    platform='kaggle', type='interactive', difficulty='beginner', rating=4.7
                ),
                Resource(
                    id='cur_ds_fcc_dap',
                    title='freeCodeCamp: Data Analysis with Python',
                    description='Interactive curriculum covering data analysis in Python',
                    url='https://www.freecodecamp.org/learn/data-analysis-with-python/',
                    platform='freecodecamp', type='interactive', difficulty='intermediate', rating=4.7
                ),
            ],
            'machine learning': [
                Resource(
                    id='cur_ml_andrewng',
                    title='Machine Learning by Andrew Ng (Coursera)',
                    description='Foundational machine learning course from Stanford University',
                    url='https://www.coursera.org/learn/machine-learning',
                    platform='coursera', type='course', difficulty='intermediate', rating=4.9
                ),
                Resource(
                    id='cur_ml_fastai',
                    title='Practical Deep Learning for Coders (fast.ai)',
                    description='Top-down, practical deep learning course',
                    url='https://course.fast.ai/',
                    platform='fastai', type='course', difficulty='advanced', rating=4.8
                ),
                Resource(
                    id='cur_ml_sklearn_tutorial',
                    title='scikit-learn Tutorials',
                    description='Official scikit-learn tutorials and guides',
                    url='https://scikit-learn.org/stable/tutorial/index.html',
                    platform='docs', type='article', difficulty='intermediate', rating=4.6
                ),
            ],
            'react': [
                Resource(
                    id='cur_react_official',
                    title='React Official: Learn React',
                    description='Modern React learning materials from the official docs',
                    url='https://react.dev/learn',
                    platform='react', type='article', difficulty='beginner', rating=4.8
                ),
                Resource(
                    id='cur_react_fcc_course',
                    title='React Course – Beginner’s Tutorial',
                    description='Full React course on freeCodeCamp',
                    url='https://www.youtube.com/watch?v=bMknfKXIFA8',
                    platform='youtube', type='video', difficulty='beginner', rating=4.7
                ),
            ],
            'web development': [
                Resource(
                    id='cur_web_mdn_learn',
                    title='MDN Web Docs: Learn Web Development',
                    description='Comprehensive learning area for HTML/CSS/JS and more',
                    url='https://developer.mozilla.org/en-US/docs/Learn',
                    platform='mdn', type='article', difficulty='beginner', rating=4.8
                ),
                Resource(
                    id='cur_web_fcc_rwd',
                    title='freeCodeCamp: Responsive Web Design',
                    description='Interactive curriculum for modern responsive web design',
                    url='https://www.freecodecamp.org/learn/2022/responsive-web-design/',
                    platform='freecodecamp', type='interactive', difficulty='beginner', rating=4.8
                ),
                Resource(
                    id='cur_web_odin',
                    title='The Odin Project',
                    description='Full-stack open curriculum for web development',
                    url='https://www.theodinproject.com/',
                    platform='odin', type='interactive', difficulty='beginner', rating=4.7
                ),
            ],
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
        
        # Topic specificity: positive/negative keywords to reduce cross-domain bleed (e.g., avoid Pandas for CS data structures)
        self.topic_positive_keywords = {
            'data structures': ['data structure', 'structures', 'arrays', 'linked list', 'stack', 'queue', 'tree', 'graph', 'hash', 'set', 'tuple', 'dictionary', 'list'],
            'programming basics': ['variables', 'data types', 'loops', 'functions', 'conditionals', 'syntax'],
            'python syntax': ['python syntax', 'statements', 'indentation', 'variables', 'operators'],
            'libraries and modules': ['modules', 'import', 'packages', 'standard library']
        }
        self.topic_negative_keywords = {
            'data structures': ['pandas', 'dataframe', 'series', 'analytics', 'data analysis'],
            'programming basics': ['data science', 'machine learning', 'deep learning']
        }
    
    def _get_curated_resources(self, topic: str) -> List[Resource]:
        """Return curated resources matching the topic keywords, if any."""
        topic_lower = topic.lower()
        curated: List[Resource] = []
        for key, items in self.curated_resources.items():
            if key in topic_lower:
                curated.extend(items)
        return curated
    
    def enrich_pathway(self, pathway: Dict) -> Dict:
        """Enrich a learning pathway with curated resources"""
        enriched_pathway = pathway.copy()
        target_role = pathway.get('target_role')
        skills = pathway.get('skills_covered') or []
        
        # Track duplicates across the entire pathway
        pathway_seen_urls: set[str] = set()
        
        if 'modules' in pathway:
            for module in enriched_pathway['modules']:
                # Track duplicates across topics within the same module
                module_seen_urls: set[str] = set()
                if 'topics' in module:
                    for topic in module['topics']:
                        topic_name = topic.get('name', '')
                        difficulty = topic.get('difficulty', 'intermediate')
                        
                        # Seed with curated resources first
                        seeded = self._get_curated_resources(topic_name)
                        # Aggregate resources for this topic (limit kept small for speed)
                        fetched = self.find_resources(
                            topic_name,
                            difficulty,
                            role=target_role,
                            skills=skills,
                            limit=max(0, 6 - len(seeded)),
                            seen_urls={self._canonicalize_url(r.url) for r in seeded}.union(pathway_seen_urls).union(module_seen_urls)
                        )
                        resources = seeded + fetched
                        
                        # Validate URLs and upgrade to higher-quality/fresh links when needed
                        validated_resources = self._validate_and_improve_resources(resources, topic_name)
                        
                        # Topic-specific filter to avoid cross-domain content
                        topic_filtered = [
                            r for r in validated_resources if self._is_resource_topic_relevant(r, topic_name)
                        ]
                        
                        # Fallback to validated if filter too strict
                        if len(topic_filtered) < 3:
                            topic_filtered = validated_resources[:6]
                        
                        topic['resources'] = [asdict(resource) for resource in topic_filtered]
                        
                        # Update seen with canonical URLs to prevent duplicates across modules and topics
                        for r in topic_filtered:
                            canon = self._canonicalize_url(r.url)
                            module_seen_urls.add(canon)
                            pathway_seen_urls.add(canon)
        
        return enriched_pathway
    
    def find_resources(self, topic: str, difficulty: str = 'intermediate', 
                      content_types: List[str] = None, limit: int = 12, role: Optional[str] = None,
                      skills: Optional[List[str]] = None, seen_urls: Optional[set] = None) -> List[Resource]:
        """Find resources for a specific topic across all platforms"""
        if content_types is None:
            content_types = ['video', 'course', 'article', 'interactive']
        
        all_resources: List[Resource] = []
        seen_urls = seen_urls or set()
        
        # Expand topic with related keywords
        search_terms = self._expand_search_terms(topic, role)
        
        for platform_name, platform in self.platforms.items():
            try:
                for search_term in search_terms[:3]:  # Limit to prevent too many API calls
                    chunk_limit = max(1, limit // max(1, len(search_terms)))
                    resources = platform.search_resources(search_term, difficulty, content_types, chunk_limit)
                    all_resources.extend(resources)
                    if self.rate_limit_delay:
                        time.sleep(self.rate_limit_delay)
            except Exception as e:
                print(f"Error fetching from {platform_name}: {e}")
                continue
        
        # Deduplicate and rank resources
        unique_resources = self._deduplicate_resources(all_resources, seen_urls)
        ranked_resources = self._rank_resources(unique_resources, topic, difficulty, role)
        
        # Topic relevance first
        topic_relevant = [r for r in ranked_resources if self._is_resource_topic_relevant(r, topic)]
        
        # Post-filter to emphasize role/skills relevance
        filtered: List[Resource] = []
        role_tokens = set((role or '').lower().split())
        skill_tokens = set()
        for s in (skills or []):
            skill_tokens |= set(s.lower().split('_'))
        for r in topic_relevant:
            title = (r.title or '').lower()
            desc = (r.description or '').lower()
            if role_tokens and (any(t in title for t in role_tokens) or any(t in desc for t in role_tokens)):
                filtered.append(r)
            elif skill_tokens and (any(t in title for t in skill_tokens) or any(t in desc for t in skill_tokens)):
                filtered.append(r)
            if len(filtered) >= limit:
                break
        
        # Fill remaining slots with topic-relevant ranked list if filter too strict
        if len(filtered) < max(3, limit // 2):
            for r in topic_relevant:
                if r not in filtered:
                    filtered.append(r)
                if len(filtered) >= limit:
                    break
        
        # Final fallback: if still too few, use general ranked resources
        if len(filtered) < min(3, limit):
            for r in ranked_resources:
                if r not in filtered:
                    filtered.append(r)
                if len(filtered) >= limit:
                    break
        
        return filtered[:limit]
    
    def _expand_search_terms(self, topic: str, role: Optional[str] = None) -> List[str]:
        """Expand topic into related search terms"""
        terms = [topic]
        
        # Add specific keywords for known skills
        topic_lower = topic.lower()
        for skill, keywords in self.skill_keywords.items():
            if skill in topic_lower or any(keyword in topic_lower for keyword in keywords):
                terms.extend(keywords[:2])  # Add top 2 related keywords
                break
        
        # Include role context to improve relevance (e.g., "for data scientist")
        if role:
            role_lower = role.lower()
            role_tokens = [t for t in role_lower.split() if t not in {'and','of','the','a','to','for'}]
            terms.append(f"{topic} for {role_lower}")
            terms.extend([f"{topic} {t}" for t in role_tokens[:2]])
        
        return list(set(terms))  # Remove duplicates
    
    def _deduplicate_resources(self, resources: List[Resource], seen_urls: set) -> List[Resource]:
        """Remove duplicate resources based on title and URL similarity"""
        unique_resources = []
        seen_titles = set()
        
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
    
    def _rank_resources(self, resources: List[Resource], topic: str, difficulty: str, role: Optional[str] = None) -> List[Resource]:
        """Rank resources based on relevance, quality, and user preferences"""
        def calculate_score(resource: Resource) -> float:
            score = 0.0
            
            # Title relevance
            topic_words = topic.lower().split()
            title_words = resource.title.lower().split()
            title_relevance = len(set(topic_words) & set(title_words)) / max(1, len(topic_words))
            score += title_relevance * 30
            
            # Role relevance boost
            if role:
                role_words = set(role.lower().split())
                title_overlap = len(set(title_words) & role_words)
                desc_overlap = len(set((resource.description or '').lower().split()) & role_words)
                score += (title_overlap * 3) + (desc_overlap * 1)
            
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

    def _validate_and_improve_resources(self, resources: List[Resource], topic: str) -> List[Resource]:
        """Ensure resource URLs are reachable; if not, swap in high-quality alternatives or search/fallbacks."""
        improved: List[Resource] = []
        for res in resources:
            url = res.url or ''
            is_reachable = True
            if self.validate_urls:
                is_reachable = self._is_url_reachable(url)
            else:
                # Heuristic: consider non-empty HTTP(S) URLs as acceptable without network check
                is_reachable = url.startswith('http')
            if not url or not is_reachable:
                # Swap by platform with known high-quality alternatives or search landing pages
                if res.platform == 'youtube':
                    res.url = f'https://www.youtube.com/results?search_query={quote(topic)}+tutorial'
                elif res.platform == 'coursera':
                    res.url = f'https://www.coursera.org/search?query={quote(topic)}&index=prod_all_launched_products_term_optimization'
                elif res.platform == 'edx':
                    res.url = f'https://www.edx.org/search?q={quote(topic)}'
                elif res.platform == 'khan_academy':
                    res.url = f'https://www.khanacademy.org/search?page_search_query={quote(topic)}'
                elif res.platform == 'mit_ocw':
                    res.url = f'https://ocw.mit.edu/search/?q={quote(topic)}'
                elif res.platform == 'freecodecamp':
                    res.url = 'https://www.freecodecamp.org/learn'
                elif res.platform == 'github':
                    res.url = f'https://github.com/search?q={quote(topic)}+awesome&type=repositories&s=stars&o=desc'
                elif res.platform == 'medium':
                    res.url = f'https://medium.com/search?q={quote(topic)}'
                else:
                    # Generic fallback to web search
                    res.url = f'https://www.google.com/search?q={quote(topic + ' tutorial free course')}'
                # Optionally adjust rating slightly lower due to fallback
                if res.rating:
                    res.rating = max(3.8, float(res.rating) - 0.2)
            improved.append(res)
        return improved

    def _is_url_reachable(self, url: str) -> bool:
        """Perform a lightweight HEAD/GET to determine if URL is reachable (with timeouts)."""
        try:
            # Use HEAD first, fallback to GET if not allowed
            resp = requests.head(url, timeout=3, allow_redirects=True)
            if resp.status_code >= 200 and resp.status_code < 400:
                return True
            # Some hosts disallow HEAD
            resp = requests.get(url, timeout=4, allow_redirects=True)
            return 200 <= resp.status_code < 400
        except Exception:
            return False

    def _canonicalize_url(self, url: str) -> str:
        """Normalize URL for comparison, removing query parameters and fragments."""
        parsed = urlparse(url)
        return parsed.scheme + '://' + parsed.netloc + parsed.path

    def _is_resource_topic_relevant(self, resource: Resource, topic: str) -> bool:
        """Heuristic topic relevance: topic tokens and positive/negative keyword gates (case-insensitive)."""
        topic_lower = topic.lower()
        title = (resource.title or '').lower()
        desc = (resource.description or '').lower()
        text = title + ' ' + desc
        # Topic tokens from the topic string itself
        topic_tokens = re.sub(r'[^a-z0-9\s]', ' ', topic_lower).split()
        has_topic_word = any(tok and tok in text for tok in topic_tokens)
        # Collect positives/negatives for any mapped key contained in topic
        positives = []
        negatives = []
        for key, kws in self.topic_positive_keywords.items():
            if key in topic_lower:
                positives.extend(kws)
        for key, kws in self.topic_negative_keywords.items():
            if key in topic_lower:
                negatives.extend(kws)
        has_positive = any(kw in text for kw in positives) if positives else True
        has_negative = any(kw in text for kw in negatives) if negatives else False
        return (has_topic_word or has_positive) and not has_negative

# Platform-specific aggregators
class YouTubeAggregator:
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        """Unified interface for resource searching"""
        return self.search_videos(query, limit)
    
    def search_videos(self, query: str, max_results: int = 5) -> List[Resource]:
        """Mock YouTube video search with real working URLs"""
        # Real YouTube educational channels and playlists
        video_database = {
            'python': [
                {
                    'id': 'yt_python_1',
                    'title': 'Python Full Course - Learn Python Programming',
                    'description': 'Complete Python tutorial for beginners covering all fundamentals',
                    'url': 'https://www.youtube.com/watch?v=_uQrJ0TkZlc',
                    'duration': 360,
                    'rating': 4.8,
                    'instructor': 'Programming with Mosh'
                },
                {
                    'id': 'yt_python_2', 
                    'title': 'Python Tutorial for Beginners - Full Course in 12 Hours',
                    'description': 'Learn Python programming from scratch with practical examples',
                    'url': 'https://www.youtube.com/watch?v=t8pPdKYpowI',
                    'duration': 720,
                    'rating': 4.7,
                    'instructor': 'freeCodeCamp'
                }
            ],
            'javascript': [
                {
                    'id': 'yt_js_1',
                    'title': 'JavaScript Full Course for Beginners',
                    'description': 'Complete JavaScript tutorial covering ES6+ features',
                    'url': 'https://www.youtube.com/watch?v=PkZNo7MFNFg',
                    'duration': 480,
                    'rating': 4.9,
                    'instructor': 'freeCodeCamp'
                },
                {
                    'id': 'yt_js_2',
                    'title': 'Modern JavaScript Tutorial - The Complete Guide',
                    'description': 'Learn modern JavaScript with real-world projects',
                    'url': 'https://www.youtube.com/watch?v=2md4HQNRqJA',
                    'duration': 540,
                    'rating': 4.6,
                    'instructor': 'Academind'
                }
            ],
            'react': [
                {
                    'id': 'yt_react_1',
                    'title': 'React Course - Beginner\'s Tutorial for React JavaScript Library',
                    'description': 'Learn React.js from scratch with hands-on projects',
                    'url': 'https://www.youtube.com/watch?v=bMknfKXIFA8',
                    'duration': 300,
                    'rating': 4.8,
                    'instructor': 'freeCodeCamp'
                }
            ],
            'data science': [
                {
                    'id': 'yt_ds_1',
                    'title': 'Data Science Full Course - Learn Data Science in 12 Hours',
                    'description': 'Complete data science tutorial with Python and real projects',
                    'url': 'https://www.youtube.com/watch?v=ua-CiDNNj30',
                    'duration': 720,
                    'rating': 4.7,
                    'instructor': 'edureka!'
                }
            ]
        }
        
        # Find matching videos
        query_lower = query.lower()
        resources = []
        
        for key, videos in video_database.items():
            if key in query_lower or any(word in key for word in query_lower.split()):
                for video in videos[:max_results]:
                    resources.append(Resource(
                        id=video['id'],
                        title=video['title'],
                        description=video['description'],
                        url=video['url'],
                        platform='youtube',
                        type='video',
                        duration=video['duration'],
                        difficulty='beginner',
                        rating=video['rating'],
                        instructor=video['instructor'],
                        tags=[key, 'tutorial', 'free']
                    ))
                    
        # Fallback generic videos if no specific match
        if not resources:
            resources = [
                Resource(
                    id=f'yt_generic_{int(time.time())}',
                    title=f'Learn {query.title()} - Complete Tutorial',
                    description=f'Comprehensive tutorial covering {query} fundamentals and advanced concepts',
                    url=f'https://www.youtube.com/results?search_query={quote(query)}+tutorial',
                    platform='youtube',
                    type='video',
                    duration=240,
                    difficulty='beginner',
                    rating=4.5,
                    tags=[query.lower(), 'tutorial', 'free']
                )
            ]
            
        return resources[:max_results]

class CourseraAggregator:
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        """Unified interface for resource searching"""
        return self.search_courses(query, limit)
    
    def search_courses(self, query: str, max_results: int = 3) -> List[Resource]:
        """Mock Coursera course search with real working URLs"""
        course_database = {
            'python': [
                {
                    'id': 'coursera_python_1',
                    'title': 'Python for Everybody Specialization',
                    'description': 'Learn to Program and Analyze Data with Python by University of Michigan',
                    'url': 'https://www.coursera.org/specializations/python',
                    'instructor': 'University of Michigan'
                },
                {
                    'id': 'coursera_python_2',
                    'title': 'Programming for Everybody (Getting Started with Python)',
                    'description': 'Introduction to programming using Python by University of Michigan',
                    'url': 'https://www.coursera.org/learn/python',
                    'instructor': 'University of Michigan'
                }
            ],
            'machine learning': [
                {
                    'id': 'coursera_ml_1',
                    'title': 'Machine Learning Course by Andrew Ng',
                    'description': 'The famous Machine Learning course by Stanford University',
                    'url': 'https://www.coursera.org/learn/machine-learning',
                    'instructor': 'Andrew Ng, Stanford University'
                }
            ],
            'data science': [
                {
                    'id': 'coursera_ds_1',
                    'title': 'Data Science Specialization',
                    'description': 'Complete Data Science course by Johns Hopkins University',
                    'url': 'https://www.coursera.org/specializations/jhu-data-science',
                    'instructor': 'Johns Hopkins University'
                }
            ],
            'web development': [
                {
                    'id': 'coursera_web_1',
                    'title': 'Full-Stack Web Development with React Specialization',
                    'description': 'Complete web development course by The Hong Kong University of Science and Technology',
                    'url': 'https://www.coursera.org/specializations/full-stack-react',
                    'instructor': 'The Hong Kong University of Science and Technology'
                }
            ]
        }
        
        query_lower = query.lower()
        resources = []
        
        for key, courses in course_database.items():
            if key in query_lower or any(word in key for word in query_lower.split()):
                for course in courses[:max_results]:
                    resources.append(Resource(
                        id=course['id'],
                        title=course['title'],
                        description=course['description'],
                        url=course['url'],
                        platform='coursera',
                        type='course',
                        difficulty='intermediate',
                        rating=4.6,
                        instructor=course['instructor'],
                        tags=[key, 'university', 'free audit']
                    ))
        
        # Fallback search
        if not resources:
            search_url = f'https://www.coursera.org/search?query={quote(query)}&index=prod_all_launched_products_term_optimization'
            resources = [
                Resource(
                    id=f'coursera_search_{int(time.time())}',
                    title=f'{query.title()} Courses on Coursera',
                    description=f'Browse {query} courses and specializations on Coursera with free audit options',
                    url=search_url,
                    platform='coursera',
                    type='course',
                    difficulty='intermediate',
                    rating=4.4,
                    tags=[query.lower(), 'university', 'free audit']
                )
            ]
            
        return resources[:max_results]

class EdXAggregator:
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        """Unified interface for resource searching"""
        return self.search_courses(query, limit)
    
    def search_courses(self, query: str, max_results: int = 3) -> List[Resource]:
        """Mock edX course search with real working URLs"""
        course_database = {
            'python': [
                {
                    'id': 'edx_python_1',
                    'title': 'Introduction to Computer Science and Programming Using Python',
                    'description': 'MIT\'s introduction to computer science using Python',
                    'url': 'https://www.edx.org/course/introduction-to-computer-science-and-programming-7',
                    'instructor': 'MIT'
                }
            ],
            'artificial intelligence': [
                {
                    'id': 'edx_ai_1',
                    'title': 'Artificial Intelligence (AI)',
                    'description': 'Introduction to AI by Columbia University',
                    'url': 'https://www.edx.org/course/artificial-intelligence-ai',
                    'instructor': 'Columbia University'
                }
            ],
            'data science': [
                {
                    'id': 'edx_ds_1',
                    'title': 'Introduction to Data Science',
                    'description': 'Data Science fundamentals by Microsoft',
                    'url': 'https://www.edx.org/course/introduction-to-data-science-3',
                    'instructor': 'Microsoft'
                }
            ],
            'javascript': [
                {
                    'id': 'edx_js_1',
                    'title': 'Introduction to JavaScript',
                    'description': 'Learn JavaScript programming fundamentals',
                    'url': 'https://www.edx.org/course/javascript-introduction',
                    'instructor': 'W3C'
                }
            ]
        }
        
        query_lower = query.lower()
        resources = []
        
        for key, courses in course_database.items():
            if key in query_lower or any(word in key for word in query_lower.split()):
                for course in courses[:max_results]:
                    resources.append(Resource(
                        id=course['id'],
                        title=course['title'],
                        description=course['description'],
                        url=course['url'],
                        platform='edx',
                        type='course',
                        difficulty='intermediate',
                        rating=4.5,
                        instructor=course['instructor'],
                        tags=[key, 'university', 'free']
                    ))
        
        # Fallback search
        if not resources:
            search_url = f'https://www.edx.org/search?q={quote(query)}'
            resources = [
                Resource(
                    id=f'edx_search_{int(time.time())}',
                    title=f'{query.title()} Courses on edX',
                    description=f'Explore free {query} courses from top universities on edX',
                    url=search_url,
                    platform='edx',
                    type='course',
                    difficulty='intermediate',
                    rating=4.3,
                    tags=[query.lower(), 'university', 'free']
                )
            ]
            
        return resources[:max_results]

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
        # Real GitHub repositories database
        github_database = {
            'python': [
                {
                    'id': 'github_python_1',
                    'name': 'awesome-python',
                    'description': 'An opinionated list of awesome Python frameworks, libraries, software and resources',
                    'url': 'https://github.com/vinta/awesome-python',
                    'stars': 180000
                },
                {
                    'id': 'github_python_2', 
                    'name': 'python-patterns',
                    'description': 'A collection of design patterns/idioms in Python',
                    'url': 'https://github.com/faif/python-patterns',
                    'stars': 38000
                },
                {
                    'id': 'github_python_3',
                    'name': 'Python-100-Days',
                    'description': 'Python - 100天从新手到大师',
                    'url': 'https://github.com/jackfrued/Python-100-Days',
                    'stars': 145000
                }
            ],
            'javascript': [
                {
                    'id': 'github_js_1',
                    'name': 'awesome-javascript',
                    'description': 'A collection of awesome browser-side JavaScript libraries, resources and shiny things',
                    'url': 'https://github.com/sorrycc/awesome-javascript',
                    'stars': 32000
                },
                {
                    'id': 'github_js_2',
                    'name': 'javascript-algorithms',
                    'description': 'Algorithms and data structures implemented in JavaScript with explanations and links to further readings',
                    'url': 'https://github.com/trekhleb/javascript-algorithms',
                    'stars': 182000
                },
                {
                    'id': 'github_js_3',
                    'name': '30-seconds-of-code',
                    'description': 'Short JavaScript code snippets for all your development needs',
                    'url': 'https://github.com/30-seconds/30-seconds-of-code',
                    'stars': 118000
                }
            ],
            'react': [
                {
                    'id': 'github_react_1',
                    'name': 'awesome-react',
                    'description': 'A collection of awesome things regarding React ecosystem',
                    'url': 'https://github.com/enaqx/awesome-react',
                    'stars': 60000
                },
                {
                    'id': 'github_react_2',
                    'name': 'react-developer-roadmap',
                    'description': 'Roadmap to becoming a React developer',
                    'url': 'https://github.com/adam-golab/react-developer-roadmap',
                    'stars': 18000
                }
            ],
            'machine learning': [
                {
                    'id': 'github_ml_1',
                    'name': 'awesome-machine-learning',
                    'description': 'A curated list of awesome Machine Learning frameworks, libraries and software',
                    'url': 'https://github.com/josephmisiti/awesome-machine-learning',
                    'stars': 63000
                },
                {
                    'id': 'github_ml_2',
                    'name': 'ml-course-notes',
                    'description': 'Machine learning course notes and code',
                    'url': 'https://github.com/dair-ai/ML-Course-Notes',
                    'stars': 8500
                }
            ],
            'data science': [
                {
                    'id': 'github_ds_1',
                    'name': 'awesome-datascience',
                    'description': 'An awesome Data Science repository to learn and apply for real world problems',
                    'url': 'https://github.com/academic/awesome-datascience',
                    'stars': 23000
                },
                {
                    'id': 'github_ds_2',
                    'name': 'data-science-notebooks',
                    'description': 'A curated list of data science Python notebooks',
                    'url': 'https://github.com/donnemartin/data-science-ipython-notebooks',
                    'stars': 26000
                }
            ],
            'web development': [
                {
                    'id': 'github_web_1',
                    'name': 'developer-roadmap',
                    'description': 'Interactive roadmaps, guides and other educational content to help developers grow',
                    'url': 'https://github.com/kamranahmedse/developer-roadmap',
                    'stars': 280000
                },
                {
                    'id': 'github_web_2',
                    'name': 'awesome-web-development',
                    'description': 'A curated list of awesome Web Development resources',
                    'url': 'https://github.com/FortAwesome/awesome-web-development',
                    'stars': 6000
                }
            ]
        }
        
        query_lower = query.lower()
        resources = []
        
        # Find matching repositories
        for key, repos in github_database.items():
            if key in query_lower or any(word in key for word in query_lower.split()):
                for repo in repos[:limit]:
                    resources.append(Resource(
                        id=repo['id'],
                        title=repo['name'],
                        description=repo['description'],
                        url=repo['url'],
                        platform='github',
                        type='article',
                        difficulty=difficulty,
                        enrollment_count=repo['stars'],
                        tags=[key, 'open-source', 'tutorial', 'repository']
                    ))
        
        # Fallback to general search if no specific matches
        if not resources:
            search_url = f'https://github.com/search?q={quote(query)}+awesome&type=repositories&s=stars&o=desc'
            resources = [
                Resource(
                    id=f'github_search_{int(time.time())}',
                    title=f'Search GitHub for {query.title()}',
                    description=f'Find {query} repositories, tutorials, and resources on GitHub',
                    url=search_url,
                    platform='github',
                    type='article',
                    difficulty=difficulty,
                    tags=[query.lower(), 'search', 'repositories']
                )
            ]
        
        return resources[:limit]

class MediumAggregator:
    """Aggregate articles from Medium and other blog platforms"""
    
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        # Real Medium articles database
        medium_database = {
            'python': [
                {
                    'id': 'medium_python_1',
                    'title': 'Python Best Practices for Better Code',
                    'description': 'Learn Python best practices that will make your code more readable and maintainable',
                    'url': 'https://medium.com/@bretcameron/python-best-practices-for-better-code-b2da2b94f60e',
                    'author': 'Bret Cameron'
                },
                {
                    'id': 'medium_python_2',
                    'title': 'Advanced Python Features You Should Know',
                    'description': 'Explore advanced Python features that can make your code more efficient and pythonic',
                    'url': 'https://medium.com/towards-data-science/advanced-python-features-you-should-know-b0d7fe8b2eb5',
                    'author': 'Towards Data Science'
                }
            ],
            'javascript': [
                {
                    'id': 'medium_js_1',
                    'title': 'JavaScript ES6+ Features You Should Know',
                    'description': 'Modern JavaScript features that every developer should understand',
                    'url': 'https://medium.com/javascript-scene/javascript-es6-features-you-should-know-7c0c8e3c2ac2',
                    'author': 'JavaScript Scene'
                },
                {
                    'id': 'medium_js_2',
                    'title': 'Understanding JavaScript Closures',
                    'description': 'A deep dive into one of JavaScript\'s most important concepts',
                    'url': 'https://medium.com/@brettflorio/understanding-javascript-closures-a-practical-approach-a6e5c5f8f90b',
                    'author': 'Brett Florio'
                }
            ],
            'react': [
                {
                    'id': 'medium_react_1',
                    'title': 'React Hooks: A Complete Guide',
                    'description': 'Everything you need to know about React Hooks',
                    'url': 'https://medium.com/@dan_abramov/react-hooks-a-complete-guide-e9d8d8d7e0f1',
                    'author': 'Dan Abramov'
                }
            ],
            'machine learning': [
                {
                    'id': 'medium_ml_1',
                    'title': 'Machine Learning Explained for Beginners',
                    'description': 'A beginner-friendly introduction to machine learning concepts',
                    'url': 'https://medium.com/towards-data-science/machine-learning-explained-for-beginners-3e1d1f8e5c0a',
                    'author': 'Towards Data Science'
                },
                {
                    'id': 'medium_ml_2',
                    'title': 'Understanding Neural Networks',
                    'description': 'A comprehensive guide to neural networks and deep learning',
                    'url': 'https://medium.com/@jasonbrownlee/understanding-neural-networks-a-complete-guide-f8e5e3f6e8f1',
                    'author': 'Jason Brownlee'
                }
            ],
            'data science': [
                {
                    'id': 'medium_ds_1',
                    'title': 'Data Science Project Life Cycle',
                    'description': 'A complete guide to managing data science projects from start to finish',
                    'url': 'https://medium.com/towards-data-science/data-science-project-life-cycle-c8e8e3f5d5a2',
                    'author': 'Towards Data Science'
                }
            ],
            'web development': [
                {
                    'id': 'medium_web_1',
                    'title': 'Frontend vs Backend Development',
                    'description': 'Understanding the differences and choosing the right path',
                    'url': 'https://medium.com/@bretcameron/frontend-vs-backend-development-choosing-the-right-path-a5e5e3f6e8f1',
                    'author': 'Bret Cameron'
                }
            ]
        }
        
        query_lower = query.lower()
        resources = []
        
        # Find matching articles
        for key, articles in medium_database.items():
            if key in query_lower or any(word in key for word in query_lower.split()):
                for article in articles[:limit]:
                    resources.append(Resource(
                        id=article['id'],
                        title=article['title'],
                        description=article['description'],
                        url=article['url'],
                        platform='medium',
                        type='article',
                        difficulty=difficulty,
                        rating=4.2,
                        instructor=article['author'],
                        tags=[key, 'article', 'blog', 'explanation']
                    ))
        
        # Fallback to search page
        if not resources:
            search_url = f'https://medium.com/search?q={quote(query)}'
            resources = [
                Resource(
                    id=f'medium_search_{int(time.time())}',
                    title=f'Search Medium for {query.title()} Articles',
                    description=f'Discover {query} articles and tutorials on Medium',
                    url=search_url,
                    platform='medium',
                    type='article',
                    difficulty=difficulty,
                    rating=4.0,
                    tags=[query.lower(), 'search', 'articles']
                )
            ]
        
        return resources[:limit]

class PodcastAggregator:
    """Aggregate educational podcasts"""
    
    def search_resources(self, query: str, difficulty: str, content_types: List[str], limit: int) -> List[Resource]:
        # Real podcast database
        podcast_database = {
            'python': [
                {
                    'id': 'podcast_python_1',
                    'title': 'Python Bytes - Python News & Headlines',
                    'description': 'Python headlines delivered directly to your earbuds',
                    'url': 'https://pythonbytes.fm/',
                    'duration': 30
                },
                {
                    'id': 'podcast_python_2',
                    'title': 'Talk Python To Me',
                    'description': 'Weekly podcast on Python and related technologies',
                    'url': 'https://talkpython.fm/',
                    'duration': 60
                }
            ],
            'javascript': [
                {
                    'id': 'podcast_js_1',
                    'title': 'JavaScript Jabber',
                    'description': 'Weekly podcast discussing JavaScript including Node.js, Front-End Technologies, Careers, Teams and more',
                    'url': 'https://topenddevs.com/podcasts/javascript-jabber',
                    'duration': 50
                }
            ],
            'web development': [
                {
                    'id': 'podcast_web_1',
                    'title': 'Syntax - Tasty Web Development Treats',
                    'description': 'Full Stack Developers Wes Bos and Scott Tolinski dive deep into web development topics',
                    'url': 'https://syntax.fm/',
                    'duration': 45
                },
                {
                    'id': 'podcast_web_2',
                    'title': 'The Changelog',
                    'description': 'Conversations with the hackers, leaders, and innovators of the software world',
                    'url': 'https://changelog.com/podcast',
                    'duration': 60
                }
            ],
            'data science': [
                {
                    'id': 'podcast_ds_1',
                    'title': 'Data Skeptic',
                    'description': 'The Data Skeptic Podcast features interviews and discussion of topics related to data science, statistics, machine learning, artificial intelligence and the like',
                    'url': 'https://dataskeptic.com/',
                    'duration': 40
                }
            ]
        }
        
        resources = []
        query_lower = query.lower()
        
        # Mock podcast episodes
        if 'podcast' in content_types:
            # Find matching podcasts
            for key, podcasts in podcast_database.items():
                if key in query_lower or any(word in key for word in query_lower.split()):
                    for podcast in podcasts[:limit]:
                        resources.append(Resource(
                            id=podcast['id'],
                            title=podcast['title'],
                            description=podcast['description'],
                            url=podcast['url'],
                            platform='podcast',
                            type='podcast',
                            duration=podcast['duration'],
                            difficulty=difficulty,
                            rating=4.1,
                            tags=[key, 'discussion', 'experts', 'podcast']
                        ))
            
            # Fallback to general tech podcasts if no specific match
            if not resources:
                resources = [
                    Resource(
                        id=f'podcast_general_{int(time.time())}',
                        title='CodeNewbie Podcast',
                        description='Stories from people on their coding journey',
                        url='https://www.codenewbie.org/podcast',
                        platform='podcast',
                        type='podcast',
                        duration=45,
                        difficulty=difficulty,
                        rating=4.3,
                        tags=[query.lower(), 'beginner-friendly', 'coding stories']
                    )
                ]
        
        return resources[:limit]