import json
import os
from typing import Dict, List, Set, Optional, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

class AchievementType(Enum):
    """Types of achievements available in the system."""
    PROJECTS = "projects"
    FILES = "files"
    ANALYSIS = "analysis"
    DUPLICATES = "duplicates"
    COLLECTION = "collection"
    EFFICIENCY = "efficiency"
    EXPLORATION = "exploration"

@dataclass
class Achievement:
    """Represents a single achievement."""
    id: str
    name: str
    description: str
    type: AchievementType
    icon: str
    points: int
    requirements: Dict[str, Any]
    unlocked: bool = False
    unlocked_at: Optional[str] = None
    progress: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.progress is None:
            self.progress = {}

class AchievementSystem:
    """
    Manages user achievements and progress tracking.
    Provides gamification elements to encourage user engagement.
    """
    
    def __init__(self, data_dir: str = "achievements"):
        self.data_dir = Path(data_dir)
        self.achievements_file = self.data_dir / "achievements.json"
        self.stats_file = self.data_dir / "stats.json"
        
        # Ensure directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize achievements
        self.achievements = self._load_achievements()
        self.stats = self._load_stats()
        
        # Subscribe to engine events (will be set by engine)
        self.engine = None
        self.event_manager = None
    
    def _load_achievements(self) -> Dict[str, Achievement]:
        """Loads or creates default achievements."""
        if self.achievements_file.exists():
            try:
                with open(self.achievements_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    achievements = {}
                    for ach_id, ach_data in data.items():
                        ach_data['type'] = AchievementType(ach_data['type'])
                        achievements[ach_id] = Achievement(**ach_data)
                    return achievements
            except Exception as e:
                print(f"AchievementSystem: Error loading achievements: {e}")
        
        # Create default achievements
        return self._create_default_achievements()
    
    def _create_default_achievements(self) -> Dict[str, Achievement]:
        """Creates the default set of achievements."""
        achievements = {
            # Project-based achievements
            "first_project": Achievement(
                id="first_project",
                name="First Steps",
                description="Load your first project",
                type=AchievementType.PROJECTS,
                icon="🚀",
                points=10,
                requirements={"projects_loaded": 1}
            ),
            "project_explorer": Achievement(
                id="project_explorer",
                name="Project Explorer",
                description="Load 5 different projects",
                type=AchievementType.PROJECTS,
                icon="🗂️",
                points=25,
                requirements={"projects_loaded": 5}
            ),
            "project_master": Achievement(
                id="project_master",
                name="Project Master",
                description="Load 25 different projects",
                type=AchievementType.PROJECTS,
                icon="👑",
                points=100,
                requirements={"projects_loaded": 25}
            ),
            
            # File-based achievements
            "file_collector": Achievement(
                id="file_collector",
                name="File Collector",
                description="Process 100 files in a single project",
                type=AchievementType.FILES,
                icon="📁",
                points=20,
                requirements={"max_files_in_project": 100}
            ),
            "file_hoarder": Achievement(
                id="file_hoarder",
                name="File Hoarder",
                description="Process 1000 files in a single project",
                type=AchievementType.FILES,
                icon="📦",
                points=50,
                requirements={"max_files_in_project": 1000}
            ),
            "format_expert": Achievement(
                id="format_expert",
                name="Format Expert",
                description="Work with 10 different file formats",
                type=AchievementType.FILES,
                icon="🔧",
                points=30,
                requirements={"unique_formats_used": 10}
            ),
            
            # Analysis achievements
            "first_analysis": Achievement(
                id="first_analysis",
                name="Code Inspector",
                description="Run your first project analysis",
                type=AchievementType.ANALYSIS,
                icon="🔍",
                points=15,
                requirements={"analyses_run": 1}
            ),
            "analysis_expert": Achievement(
                id="analysis_expert",
                name="Analysis Expert",
                description="Run 50 project analyses",
                type=AchievementType.ANALYSIS,
                icon="📊",
                points=75,
                requirements={"analyses_run": 50}
            ),
            "language_polyglot": Achievement(
                id="language_polyglot",
                name="Language Polyglot",
                description="Analyze projects with 5+ programming languages",
                type=AchievementType.ANALYSIS,
                icon="🌍",
                points=40,
                requirements={"max_languages_in_project": 5}
            ),
            
            # Duplicate detection achievements
            "duplicate_hunter": Achievement(
                id="duplicate_hunter",
                name="Duplicate Hunter",
                description="Find duplicates in a project",
                type=AchievementType.DUPLICATES,
                icon="🎯",
                points=20,
                requirements={"duplicate_searches_run": 1}
            ),
            "duplicate_expert": Achievement(
                id="duplicate_expert",
                name="Duplicate Expert",
                description="Find duplicates in 10 projects",
                type=AchievementType.DUPLICATES,
                icon="🔎",
                points=60,
                requirements={"duplicate_searches_run": 10}
            ),
            "code_cleaner": Achievement(
                id="code_cleaner",
                name="Code Cleaner",
                description="Find and resolve 100 duplicate code blocks",
                type=AchievementType.DUPLICATES,
                icon="🧹",
                points=80,
                requirements={"duplicate_blocks_found": 100}
            ),
            
            # Collection achievements
            "first_collection": Achievement(
                id="first_collection",
                name="Code Collector",
                description="Create your first code collection",
                type=AchievementType.COLLECTION,
                icon="📝",
                points=15,
                requirements={"collections_created": 1}
            ),
            "collection_master": Achievement(
                id="collection_master",
                name="Collection Master",
                description="Create 25 code collections",
                type=AchievementType.COLLECTION,
                icon="📚",
                points=75,
                requirements={"collections_created": 25}
            ),
            "format_explorer": Achievement(
                id="format_explorer",
                name="Format Explorer",
                description="Export code in all three formats (TXT, MD, HTML)",
                type=AchievementType.COLLECTION,
                icon="🎨",
                points=35,
                requirements={"formats_used": ["txt", "md", "html"]}
            ),
            
            # Efficiency achievements
            "speed_demon": Achievement(
                id="speed_demon",
                name="Speed Demon",
                description="Process a project with 100+ files in under 30 seconds",
                type=AchievementType.EFFICIENCY,
                icon="⚡",
                points=50,
                requirements={"fast_processing": {"files": 100, "time": 30}}
            ),
            "memory_master": Achievement(
                id="memory_master",
                name="Memory Master",
                description="Process a 1GB+ project without errors",
                type=AchievementType.EFFICIENCY,
                icon="💾",
                points=60,
                requirements={"large_project_size": 1073741824}  # 1GB in bytes
            ),
            
            # Exploration achievements
            "deep_diver": Achievement(
                id="deep_diver",
                name="Deep Diver",
                description="Analyze a project with directory depth of 10+ levels",
                type=AchievementType.EXPLORATION,
                icon="🌊",
                points=45,
                requirements={"max_directory_depth": 10}
            ),
            "binary_explorer": Achievement(
                id="binary_explorer",
                name="Binary Explorer",
                description="Process a project containing 50+ binary files",
                type=AchievementType.EXPLORATION,
                icon="🔬",
                points=55,
                requirements={"binary_files_processed": 50}
            )
        }
        
        # Save default achievements
        self._save_achievements(achievements)
        return achievements
    
    def _load_stats(self) -> Dict[str, Any]:
        """Loads user statistics."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"AchievementSystem: Error loading stats: {e}")
        
        # Return default stats
        return {
            "projects_loaded": 0,
            "total_files_processed": 0,
            "max_files_in_project": 0,
            "unique_formats_used": set(),
            "analyses_run": 0,
            "max_languages_in_project": 0,
            "duplicate_searches_run": 0,
            "duplicate_blocks_found": 0,
            "collections_created": 0,
            "formats_used": set(),
            "fast_processing": {"files": 0, "time": float('inf')},
            "max_project_size": 0,
            "max_directory_depth": 0,
            "binary_files_processed": 0,
            "total_points": 0,
            "achievements_unlocked": 0,
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_achievements(self, achievements: Dict[str, Achievement]):
        """Saves achievements to file."""
        try:
            data = {}
            for ach_id, achievement in achievements.items():
                ach_dict = asdict(achievement)
                ach_dict['type'] = achievement.type.value
                data[ach_id] = ach_dict
            
            with open(self.achievements_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"AchievementSystem: Error saving achievements: {e}")
    
    def _save_stats(self):
        """Saves statistics to file."""
        try:
            # Convert sets to lists for JSON serialization
            stats_copy = self.stats.copy()
            for key, value in stats_copy.items():
                if isinstance(value, set):
                    stats_copy[key] = list(value)
            
            stats_copy["last_updated"] = datetime.now().isoformat()
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_copy, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"AchievementSystem: Error saving stats: {e}")
    
    def set_engine(self, engine, event_manager):
        """Sets the engine and event manager for event subscription."""
        self.engine = engine
        self.event_manager = event_manager
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        """Subscribes to relevant engine events."""
        if self.event_manager:
            # Import events here to avoid circular imports
            from ..events import PROJECT_LOADED, ANALYSIS_COMPLETE, COLLECTION_COMPLETE
            
            self.event_manager.subscribe(PROJECT_LOADED, self.on_project_loaded)
            self.event_manager.subscribe(ANALYSIS_COMPLETE, self.on_analysis_complete)
            self.event_manager.subscribe(COLLECTION_COMPLETE, self.on_collection_complete)
    
    def on_project_loaded(self, data=None):
        """Handles project loaded events."""
        if not self.engine:
            return
        
        # Update project statistics
        self.stats["projects_loaded"] += 1
        
        # Update file statistics
        total_files = len(self.engine.state.all_discovered_files)
        self.stats["total_files_processed"] += total_files
        self.stats["max_files_in_project"] = max(
            self.stats["max_files_in_project"], 
            total_files
        )
        
        # Update format statistics
        if self.engine.state.active_formats:
            self.stats["unique_formats_used"].update(self.engine.state.active_formats)
        
        # Update project size
        total_size = sum(
            os.path.getsize(f) for f in self.engine.state.all_discovered_files 
            if os.path.exists(f)
        )
        self.stats["max_project_size"] = max(
            self.stats["max_project_size"], 
            total_size
        )
        
        self._save_stats()
        self._check_achievements()
    
    def on_analysis_complete(self, data=None):
        """Handles analysis complete events."""
        if not data:
            return
        
        # Update analysis statistics
        self.stats["analyses_run"] += 1
        
        # Update language statistics
        if "languages" in data:
            languages_count = data["languages"].get("total_languages", 0)
            self.stats["max_languages_in_project"] = max(
                self.stats["max_languages_in_project"],
                languages_count
            )
        
        # Update duplicate statistics
        if data.get("type") == "duplicates":
            self.stats["duplicate_searches_run"] += 1
            if "results" in data:
                duplicate_blocks = data["results"].get("duplicate_blocks", {})
                self.stats["duplicate_blocks_found"] += len(duplicate_blocks)
        
        # Update structure statistics
        if "structure" in data:
            depth = data["structure"].get("depth", 0)
            self.stats["max_directory_depth"] = max(
                self.stats["max_directory_depth"],
                depth
            )
        
        self._save_stats()
        self._check_achievements()
    
    def on_collection_complete(self, data=None):
        """Handles collection complete events."""
        # Update collection statistics
        self.stats["collections_created"] += 1
        
        # Update format usage statistics
        if self.engine and hasattr(self.engine, 'state'):
            # Try to determine format from output path
            if data and isinstance(data, str):
                ext = Path(data).suffix.lower()
                if ext in ['.txt', '.md', '.html']:
                    format_type = ext[1:]  # Remove dot
                    self.stats["formats_used"].add(format_type)
        
        self._save_stats()
        self._check_achievements()
    
    def _check_achievements(self):
        """Checks if any achievements should be unlocked."""
        newly_unlocked = []
        
        for achievement in self.achievements.values():
            if not achievement.unlocked and self._check_achievement_requirements(achievement):
                achievement.unlocked = True
                achievement.unlocked_at = datetime.now().isoformat()
                newly_unlocked.append(achievement)
                
                # Update statistics
                self.stats["total_points"] += achievement.points
                self.stats["achievements_unlocked"] += 1
        
        if newly_unlocked:
            self._save_achievements(self.achievements)
            self._save_stats()
            self._notify_achievements(newly_unlocked)
    
    def _check_achievement_requirements(self, achievement: Achievement) -> bool:
        """Checks if an achievement's requirements are met."""
        requirements = achievement.requirements
        
        for req_key, req_value in requirements.items():
            if req_key not in self.stats:
                return False
            
            current_value = self.stats[req_key]
            
            if isinstance(req_value, dict):
                # Handle complex requirements like fast_processing
                if req_key == "fast_processing":
                    if not self._check_fast_processing(req_value):
                        return False
                else:
                    # Handle other dict requirements
                    for sub_key, sub_value in req_value.items():
                        if sub_key not in current_value or current_value[sub_key] < sub_value:
                            return False
            elif isinstance(req_value, list):
                # Handle list requirements like formats_used
                if req_key == "formats_used":
                    if not all(fmt in current_value for fmt in req_value):
                        return False
                else:
                    if current_value < req_value:
                        return False
            else:
                # Handle simple numeric requirements
                if current_value < req_value:
                    return False
        
        return True
    
    def _check_fast_processing(self, requirements: Dict[str, Any]) -> bool:
        """Checks fast processing requirements."""
        # This would need to be implemented with timing data
        # For now, return False to indicate not yet achieved
        return False
    
    def _notify_achievements(self, achievements: List[Achievement]):
        """Notifies about newly unlocked achievements."""
        for achievement in achievements:
            print(f"🏆 Achievement Unlocked: {achievement.name} ({achievement.icon})")
            print(f"   {achievement.description}")
            print(f"   Points: +{achievement.points}")
            print()
    
    def get_achievement(self, achievement_id: str) -> Optional[Achievement]:
        """Gets an achievement by ID."""
        return self.achievements.get(achievement_id)
    
    def get_all_achievements(self) -> List[Achievement]:
        """Gets all achievements."""
        return list(self.achievements.values())
    
    def get_unlocked_achievements(self) -> List[Achievement]:
        """Gets all unlocked achievements."""
        return [a for a in self.achievements.values() if a.unlocked]
    
    def get_locked_achievements(self) -> List[Achievement]:
        """Gets all locked achievements."""
        return [a for a in self.achievements.values() if not a.unlocked]
    
    def get_achievements_by_type(self, achievement_type: AchievementType) -> List[Achievement]:
        """Gets achievements by type."""
        return [a for a in self.achievements.values() if a.type == achievement_type]
    
    def get_total_points(self) -> int:
        """Gets total points earned."""
        return self.stats["total_points"]
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Gets a summary of achievement progress."""
        total_achievements = len(self.achievements)
        unlocked_achievements = len(self.get_unlocked_achievements())
        
        return {
            "total_achievements": total_achievements,
            "unlocked_achievements": unlocked_achievements,
            "locked_achievements": total_achievements - unlocked_achievements,
            "completion_percentage": (unlocked_achievements / total_achievements * 100) if total_achievements > 0 else 0,
            "total_points": self.get_total_points(),
            "stats": self.stats.copy()
        }
    
    def reset_progress(self):
        """Resets all achievement progress."""
        for achievement in self.achievements.values():
            achievement.unlocked = False
            achievement.unlocked_at = None
        
        self.stats = self._load_stats()
        self._save_achievements(self.achievements)
        self._save_stats()
    
    def unlock_achievement(self, achievement_id: str):
        """Manually unlocks an achievement (for testing)."""
        achievement = self.achievements.get(achievement_id)
        if achievement and not achievement.unlocked:
            achievement.unlocked = True
            achievement.unlocked_at = datetime.now().isoformat()
            self.stats["total_points"] += achievement.points
            self.stats["achievements_unlocked"] += 1
            
            self._save_achievements(self.achievements)
            self._save_stats()
            self._notify_achievements([achievement])


# Global instance for easy access
_achievement_system = None

def get_achievement_system() -> AchievementSystem:
    """Returns the global achievement system instance."""
    global _achievement_system
    if _achievement_system is None:
        _achievement_system = AchievementSystem()
    return _achievement_system
