"""
Backtest Template Manager
==========================

Management system for backtest templates with:
- Template CRUD operations
- Version control
- Sharing and collaboration
- Template validation
- Dynamic template loading

Author: CBSC Quant Team
Version: 1.0.0
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
import hashlib
from pathlib import Path
import yaml
import aiofiles
import os

logger = logging.getLogger(__name__)


class TemplateStatus(str, Enum):
    """Template status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class TemplateAccess(str, Enum):
    """Template access levels"""
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"


@dataclass
class TemplateParameter:
    """Template parameter definition"""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    default_value: Any
    description: str
    required: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    choices: Optional[List[Any]] = None
    validation_regex: Optional[str] = None


@dataclass
class TemplateVersion:
    """Template version information"""
    version: str
    changelog: str
    created_at: datetime
    created_by: str
    compatibility: List[str] = field(default_factory=list)  # Compatible previous versions


@dataclass
class BacktestTemplate:
    """Complete backtest template"""
    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    author: str
    author_id: str
    status: TemplateStatus = TemplateStatus.DRAFT
    access: TemplateAccess = TemplateAccess.PRIVATE

    # Template content
    strategy_type: str
    strategy_config: Dict[str, Any]
    parameters: List[TemplateParameter]
    risk_settings: Dict[str, Any]
    data_requirements: Dict[str, Any]

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    # Version control
    current_version: str = "1.0.0"
    versions: List[TemplateVersion] = field(default_factory=list)

    # Usage statistics
    usage_count: int = 0
    rating: float = 0.0
    rating_count: int = 0

    # Collaboration
    collaborators: List[str] = field(default_factory=list)
    parent_template_id: Optional[str] = None
    forked_from: Optional[str] = None


class TemplateManager:
    """Template management system"""

    def __init__(self, storage_path: str = "./templates"):
        """
        Initialize template manager

        Args:
            storage_path: Path to store template files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.templates: Dict[str, BacktestTemplate] = {}
        self.index_file = self.storage_path / "index.json"

        # Template categories
        self.categories = [
            "trend_following",
            "mean_reversion",
            "momentum",
            "arbitrage",
            "market_making",
            "statistical_arbitrage",
            "event_driven",
            "custom"
        ]

        # Load existing templates
        asyncio.create_task(self._load_templates())

    async def create_template(
        self,
        name: str,
        description: str,
        category: str,
        strategy_type: str,
        strategy_config: Dict[str, Any],
        parameters: List[Dict[str, Any]],
        author: str,
        author_id: str,
        tags: Optional[List[str]] = None,
        access: TemplateAccess = TemplateAccess.PRIVATE
    ) -> BacktestTemplate:
        """
        Create a new backtest template

        Args:
            name: Template name
            description: Template description
            category: Template category
            strategy_type: Type of strategy
            strategy_config: Strategy configuration
            parameters: Template parameters
            author: Author name
            author_id: Author ID
            tags: Template tags
            access: Access level

        Returns:
            Created template
        """
        # Validate category
        if category not in self.categories:
            raise ValueError(f"Invalid category. Valid categories: {self.categories}")

        # Convert parameters to TemplateParameter objects
        template_params = []
        for param in parameters:
            template_params.append(TemplateParameter(**param))

        # Create template
        template = BacktestTemplate(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            author=author,
            author_id=author_id,
            access=access,
            strategy_type=strategy_type,
            strategy_config=strategy_config,
            parameters=template_params,
            risk_settings={},
            data_requirements={},
            versions=[
                TemplateVersion(
                    version="1.0.0",
                    changelog="Initial version",
                    created_at=datetime.utcnow(),
                    created_by=author_id
                )
            ]
        )

        # Validate template
        await self._validate_template(template)

        # Save template
        await self._save_template(template)
        self.templates[template.id] = template

        logger.info(f"Created template: {template.id} - {name}")
        return template

    async def get_template(self, template_id: str, user_id: Optional[str] = None) -> Optional[BacktestTemplate]:
        """
        Get template by ID

        Args:
            template_id: Template ID
            user_id: User ID for access control

        Returns:
            Template or None if not found
        """
        template = self.templates.get(template_id)
        if not template:
            return None

        # Check access permissions
        if not self._can_access(template, user_id):
            return None

        # Increment usage count
        template.usage_count += 1
        await self._save_template(template)

        return template

    async def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any],
        user_id: str,
        create_version: bool = True
    ) -> Optional[BacktestTemplate]:
        """
        Update template

        Args:
            template_id: Template ID
            updates: Updates to apply
            user_id: User ID making the update
            create_version: Whether to create a new version

        Returns:
            Updated template or None if not found
        """
        template = self.templates.get(template_id)
        if not template:
            return None

        # Check edit permissions
        if not self._can_edit(template, user_id):
            raise PermissionError("User does not have edit permissions")

        # Apply updates
        for key, value in updates.items():
            if key == "parameters" and isinstance(value, list):
                # Convert parameter dictionaries to TemplateParameter objects
                template.parameters = [TemplateParameter(**p) for p in value]
            elif hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = datetime.utcnow()

        # Create new version if requested
        if create_version:
            new_version = self._increment_version(template.current_version)
            template.versions.append(
                TemplateVersion(
                    version=new_version,
                    changelog=updates.get("changelog", "Updated template"),
                    created_at=datetime.utcnow(),
                    created_by=user_id,
                    compatibility=[template.current_version]
                )
            )
            template.current_version = new_version

        # Validate updated template
        await self._validate_template(template)

        # Save template
        await self._save_template(template)

        logger.info(f"Updated template: {template_id}")
        return template

    async def delete_template(self, template_id: str, user_id: str) -> bool:
        """
        Delete template

        Args:
            template_id: Template ID
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        template = self.templates.get(template_id)
        if not template:
            return False

        # Check delete permissions (only author can delete)
        if template.author_id != user_id:
            raise PermissionError("Only template author can delete template")

        # Delete template file
        template_file = self.storage_path / f"{template_id}.json"
        if template_file.exists():
            template_file.unlink()

        # Remove from memory
        del self.templates[template_id]

        logger.info(f"Deleted template: {template_id}")
        return True

    async def list_templates(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[TemplateStatus] = None,
        access: Optional[TemplateAccess] = None,
        author_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[BacktestTemplate], int]:
        """
        List templates with filters

        Args:
            user_id: User ID for access control
            category: Filter by category
            tags: Filter by tags (must match all)
            status: Filter by status
            access: Filter by access level
            author_id: Filter by author
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (templates, total_count)
        """
        filtered_templates = []

        for template in self.templates.values():
            # Check access permissions
            if not self._can_access(template, user_id):
                continue

            # Apply filters
            if category and template.category != category:
                continue
            if status and template.status != status:
                continue
            if access and template.access != access:
                continue
            if author_id and template.author_id != author_id:
                continue
            if tags and not all(tag in template.tags for tag in tags):
                continue

            filtered_templates.append(template)

        # Sort by updated date (newest first)
        filtered_templates.sort(key=lambda t: t.updated_at, reverse=True)

        # Apply pagination
        total_count = len(filtered_templates)
        paginated_templates = filtered_templates[offset:offset + limit]

        return paginated_templates, total_count

    async def search_templates(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[BacktestTemplate]:
        """
        Search templates by text query

        Args:
            query: Search query
            user_id: User ID for access control
            limit: Maximum number of results

        Returns:
            Matching templates
        """
        query_lower = query.lower()
        matching_templates = []

        for template in self.templates.values():
            # Check access permissions
            if not self._can_access(template, user_id):
                continue

            # Search in name, description, and tags
            searchable_text = (
                template.name.lower() + " " +
                template.description.lower() + " " +
                " ".join(template.tags).lower()
            )

            if query_lower in searchable_text:
                matching_templates.append(template)

        # Sort by relevance and usage
        matching_templates.sort(
            key=lambda t: (t.name.lower().startswith(query_lower), t.usage_count),
            reverse=True
        )

        return matching_templates[:limit]

    async def fork_template(
        self,
        template_id: str,
        user_id: str,
        author: str,
        new_name: Optional[str] = None
    ) -> Optional[BacktestTemplate]:
        """
        Fork an existing template

        Args:
            template_id: Template ID to fork
            user_id: User ID forking the template
            author: Author name for forked template
            new_name: Optional new name for forked template

        Returns:
            Forked template or None if not found
        """
        original = self.templates.get(template_id)
        if not original:
            return None

        # Check access permissions
        if not self._can_access(original, user_id):
            raise PermissionError("Cannot fork template - access denied")

        # Create fork
        fork = BacktestTemplate(
            id=str(uuid.uuid4()),
            name=new_name or f"{original.name} (Fork)",
            description=f"Forked from {original.name}",
            category=original.category,
            tags=original.tags.copy(),
            author=author,
            author_id=user_id,
            access=TemplateAccess.PRIVATE,
            strategy_type=original.strategy_type,
            strategy_config=original.strategy_config.copy(),
            parameters=[TemplateParameter(**asdict(p)) for p in original.parameters],
            risk_settings=original.risk_settings.copy(),
            data_requirements=original.data_requirements.copy(),
            parent_template_id=template_id,
            forked_from=template_id
        )

        # Save fork
        await self._save_template(fork)
        self.templates[fork.id] = fork

        logger.info(f"Forked template: {fork.id} from {template_id}")
        return fork

    async def rate_template(
        self,
        template_id: str,
        user_id: str,
        rating: int  # 1-5
    ) -> Optional[float]:
        """
        Rate a template

        Args:
            template_id: Template ID
            user_id: User ID
            rating: Rating (1-5)

        Returns:
            New average rating or None if not found
        """
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        template = self.templates.get(template_id)
        if not template:
            return None

        # Store rating (in production, use a database)
        rating_file = self.storage_path / f"{template_id}_ratings.json"
        ratings = {}

        if rating_file.exists():
            async with aiofiles.open(rating_file, 'r') as f:
                content = await f.read()
                ratings = json.loads(content)

        # Update or add rating
        ratings[user_id] = rating

        # Calculate new average
        template.rating = sum(ratings.values()) / len(ratings.values())
        template.rating_count = len(ratings)

        # Save ratings
        async with aiofiles.open(rating_file, 'w') as f:
            await f.write(json.dumps(ratings, indent=2))

        # Save template
        await self._save_template(template)

        logger.info(f"Rated template {template_id}: {rating}/5")
        return template.rating

    async def get_popular_templates(self, limit: int = 10) -> List[BacktestTemplate]:
        """
        Get popular templates

        Args:
            limit: Maximum number of templates

        Returns:
            Popular templates sorted by usage and rating
        """
        # Filter public templates
        public_templates = [
            t for t in self.templates.values()
            if t.access == TemplateAccess.PUBLIC and t.status == TemplateStatus.PUBLISHED
        ]

        # Sort by popularity score (usage * rating)
        def popularity_score(t):
            usage_score = min(t.usage_count / 100, 1.0)  # Normalize to 0-1
            rating_score = t.rating / 5.0  # Normalize to 0-1
            return usage_score * 0.6 + rating_score * 0.4  # Weighted average

        public_templates.sort(key=popularity_score, reverse=True)
        return public_templates[:limit]

    async def _load_templates(self):
        """Load all templates from storage"""
        if not self.index_file.exists():
            return

        # Load index
        async with aiofiles.open(self.index_file, 'r') as f:
            index_data = json.loads(await f.read())

        # Load each template
        for template_id in index_data.get("templates", []):
            template_file = self.storage_path / f"{template_id}.json"
            if template_file.exists():
                try:
                    async with aiofiles.open(template_file, 'r') as f:
                        content = await f.read()
                        template_dict = json.loads(content)

                    # Convert dict to BacktestTemplate
                    template = self._dict_to_template(template_dict)
                    self.templates[template_id] = template

                except Exception as e:
                    logger.error(f"Failed to load template {template_id}: {e}")

        logger.info(f"Loaded {len(self.templates)} templates")

    async def _save_template(self, template: BacktestTemplate):
        """Save template to storage"""
        # Save individual template
        template_file = self.storage_path / f"{template.id}.json"
        template_dict = self._template_to_dict(template)

        async with aiofiles.open(template_file, 'w') as f:
            await f.write(json.dumps(template_dict, indent=2, default=str))

        # Update index
        await self._update_index()

    async def _update_index(self):
        """Update template index file"""
        index_data = {
            "templates": list(self.templates.keys()),
            "last_updated": datetime.utcnow().isoformat()
        }

        async with aiofiles.open(self.index_file, 'w') as f:
            await f.write(json.dumps(index_data, indent=2))

    def _template_to_dict(self, template: BacktestTemplate) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return asdict(template)

    def _dict_to_template(self, template_dict: Dict[str, Any]) -> BacktestTemplate:
        """Convert dictionary to BacktestTemplate"""
        # Handle nested objects
        if "parameters" in template_dict:
            template_dict["parameters"] = [
                TemplateParameter(**p) for p in template_dict["parameters"]
            ]

        if "versions" in template_dict:
            template_dict["versions"] = [
                TemplateVersion(**v) for v in template_dict["versions"]
            ]

        # Handle date strings
        if "created_at" in template_dict and isinstance(template_dict["created_at"], str):
            template_dict["created_at"] = datetime.fromisoformat(template_dict["created_at"])
        if "updated_at" in template_dict and isinstance(template_dict["updated_at"], str):
            template_dict["updated_at"] = datetime.fromisoformat(template_dict["updated_at"])
        if "published_at" in template_dict and template_dict["published_at"]:
            template_dict["published_at"] = datetime.fromisoformat(template_dict["published_at"])

        return BacktestTemplate(**template_dict)

    async def _validate_template(self, template: BacktestTemplate):
        """Validate template configuration"""
        # Validate required fields
        if not template.name or not template.description:
            raise ValueError("Template name and description are required")

        if template.category not in self.categories:
            raise ValueError(f"Invalid category: {template.category}")

        # Validate parameters
        if not template.parameters:
            raise ValueError("Template must have at least one parameter")

        for param in template.parameters:
            if not param.name or not param.type:
                raise ValueError("Parameter name and type are required")

            # Validate parameter type
            valid_types = ["string", "number", "boolean", "array", "object"]
            if param.type not in valid_types:
                raise ValueError(f"Invalid parameter type: {param.type}")

    def _can_access(self, template: BacktestTemplate, user_id: Optional[str]) -> bool:
        """Check if user can access template"""
        if template.access == TemplateAccess.PUBLIC:
            return True
        if not user_id:
            return False
        if template.author_id == user_id:
            return True
        if user_id in template.collaborators:
            return True
        return False

    def _can_edit(self, template: BacktestTemplate, user_id: str) -> bool:
        """Check if user can edit template"""
        if template.author_id == user_id:
            return True
        if user_id in template.collaborators:
            return True
        return False

    def _increment_version(self, current_version: str) -> str:
        """Increment version number"""
        try:
            parts = current_version.split('.')
            patch = int(parts[2]) + 1
            return f"{parts[0]}.{parts[1]}.{patch}"
        except:
            return "1.0.0"


# Singleton instance
template_manager = TemplateManager()


# Example usage
if __name__ == "__main__":
    async def example_usage():
        # Create a sample template
        template = await template_manager.create_template(
            name="MA Crossover Strategy",
            description="Simple moving average crossover strategy",
            category="trend_following",
            strategy_type="ma_cross",
            strategy_config={
                "indicators": ["SMA", "EMA"],
                "signals": ["crossover", "divergence"]
            },
            parameters=[
                {
                    "name": "short_period",
                    "type": "number",
                    "default_value": 20,
                    "description": "Short moving average period",
                    "min_value": 5,
                    "max_value": 50
                },
                {
                    "name": "long_period",
                    "type": "number",
                    "default_value": 50,
                    "description": "Long moving average period",
                    "min_value": 20,
                    "max_value": 200
                }
            ],
            author="John Doe",
            author_id="user123",
            tags=["trend", "moving_average", "cross"],
            access="public"
        )

        print(f"Created template: {template.id}")

        # List templates
        templates, total = await template_manager.list_templates(limit=10)
        print(f"Found {total} templates")

        # Search templates
        search_results = await template_manager.search_templates("moving average")
        print(f"Search results: {len(search_results)} templates")

    # Run example
    asyncio.run(example_usage())