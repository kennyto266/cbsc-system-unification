"""
Strategy Version Control Service

Implements version control for strategy configurations with history tracking,
comparison, and rollback functionality.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4
from enum import Enum
import difflib
import logging

from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.strategy_models_v2 import (
    Strategy, StrategyVersion, StrategyChangeLog, StrategyStatus
)
from schemas.strategy_schemas import (
    StrategyVersionCreate, StrategyUpdate,
    StrategyVersionResponse, StrategyComparisonResult
)
from core.exceptions import StrategyError, StrategyNotFoundError, StrategyValidationError

logger = logging.getLogger(__name__)


class VersionStatus(str, Enum):
    """Version status enumeration"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ChangeType(str, Enum):
    """Change type enumeration"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PUBLISH = "publish"
    ARCHIVE = "archive"
    ROLLBACK = "rollback"


class StrategyVersionControl:
    """
    Strategy version control service

    Manages strategy configuration versions, change history,
    comparisons, and rollback operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_version(
        self,
        strategy_id: UUID,
        config: Dict[str, Any],
        version_number: Optional[str] = None,
        description: Optional[str] = None,
        status: VersionStatus = VersionStatus.DRAFT,
        author_id: Optional[UUID] = None,
        change_type: ChangeType = ChangeType.UPDATE,
        parent_version_id: Optional[UUID] = None
    ) -> StrategyVersion:
        """
        Create a new strategy version

        Args:
            strategy_id: ID of the strategy
            config: Strategy configuration
            version_number: Optional version number (auto-generated if not provided)
            description: Optional version description
            status: Version status
            author_id: ID of the author
            change_type: Type of change
            parent_version_id: Parent version ID for branching

        Returns:
            StrategyVersion: Created version
        """
        try:
            # Get strategy
            strategy = await self.db.get(Strategy, strategy_id)
            if not strategy:
                raise StrategyNotFoundError(f"Strategy {strategy_id} not found")

            # Generate version number if not provided
            if not version_number:
                version_number = await self._generate_version_number(strategy_id)

            # Check for duplicate version number
            existing = await self.db.execute(
                select(StrategyVersion).where(
                    StrategyVersion.strategy_id == strategy_id,
                    StrategyVersion.version_number == version_number
                )
            )
            if existing.scalar_one_or_none():
                raise StrategyValidationError(
                    f"Version {version_number} already exists for strategy {strategy_id}"
                )

            # Get current config for comparison
            current_config = await self._get_current_config(strategy_id)

            # Calculate changes
            changes = self._calculate_changes(current_config, config, change_type)

            # Create version
            version = StrategyVersion(
                id=uuid4(),
                strategy_id=strategy_id,
                version_number=version_number,
                config=config,
                description=description or f"Version {version_number}",
                status=status,
                parent_version_id=parent_version_id,
                author_id=author_id,
                changes=changes,
                created_at=datetime.utcnow()
            )

            self.db.add(version)

            # Create change log entry
            await self._create_change_log(
                strategy_id=strategy_id,
                version_id=version.id,
                change_type=change_type,
                description=description,
                author_id=author_id,
                changes=changes
            )

            await self.db.commit()
            await self.db.refresh(version)

            logger.info(f"Created strategy version: {strategy_id} v{version_number}")
            return version

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create version: {e}")
            raise StrategyError(f"Version creation failed: {e}") from e

    async def get_version(self, version_id: UUID) -> StrategyVersion:
        """Get strategy version by ID"""
        version = await self.db.get(StrategyVersion, version_id)
        if not version:
            raise StrategyNotFoundError(f"Version {version_id} not found")
        return version

    async def get_version_by_number(self, strategy_id: UUID, version_number: str) -> StrategyVersion:
        """Get strategy version by version number"""
        result = await self.db.execute(
            select(StrategyVersion).where(
                StrategyVersion.strategy_id == strategy_id,
                StrategyVersion.version_number == version_number
            )
        )
        version = result.scalar_one_or_none()
        if not version:
            raise StrategyNotFoundError(f"Version {version_number} not found for strategy {strategy_id}")
        return version

    async def list_versions(
        self,
        strategy_id: UUID,
        status: Optional[VersionStatus] = None,
        author_id: Optional[UUID] = None,
        include_deprecated: bool = False
    ) -> List[StrategyVersion]:
        """
        List strategy versions

        Args:
            strategy_id: ID of the strategy
            status: Optional status filter
            author_id: Optional author filter
            include_deprecated: Whether to include deprecated versions

        Returns:
            List of strategy versions
        """
        query = select(StrategyVersion).where(
            StrategyVersion.strategy_id == strategy_id
        )

        # Apply filters
        if status:
            query = query.where(StrategyVersion.status == status)

        if author_id:
            query = query.where(StrategyVersion.author_id == author_id)

        if not include_deprecated:
            query = query.where(StrategyVersion.status != VersionStatus.DEPRECATED)

        # Order by creation date (newest first)
        query = query.order_by(desc(StrategyVersion.created_at))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_latest_version(self, strategy_id: UUID, published_only: bool = False) -> Optional[StrategyVersion]:
        """
        Get the latest version of a strategy

        Args:
            strategy_id: ID of the strategy
            published_only: Whether to only return published versions

        Returns:
            Latest version or None if no versions exist
        """
        query = select(StrategyVersion).where(
            StrategyVersion.strategy_id == strategy_id
        )

        if published_only:
            query = query.where(StrategyVersion.status == VersionStatus.PUBLISHED)
        else:
            query = query.where(StrategyVersion.status != VersionStatus.DEPRECATED)

        query = query.order_by(desc(StrategyVersion.created_at)).limit(1)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_version_status(
        self,
        version_id: UUID,
        status: VersionStatus,
        author_id: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> StrategyVersion:
        """
        Update version status

        Args:
            version_id: ID of the version
            status: New status
            author_id: ID of the author making the change
            notes: Optional notes about the status change

        Returns:
            Updated version
        """
        try:
            version = await self.get_version(version_id)
            old_status = version.status

            # Validate status transitions
            if not self._is_valid_status_transition(old_status, status):
                raise StrategyValidationError(
                    f"Invalid status transition: {old_status} -> {status}"
                )

            # Update status
            version.status = status
            version.updated_at = datetime.utcnow()

            # If publishing, update strategy current version
            if status == VersionStatus.PUBLISHED:
                strategy = await self.db.get(Strategy, version.strategy_id)
                if strategy:
                    strategy.current_version_id = version.id
                    strategy.version = version.version_number

            # Create change log entry
            await self._create_change_log(
                strategy_id=version.strategy_id,
                version_id=version_id,
                change_type=ChangeType.UPDATE,
                description=f"Status changed from {old_status} to {status}",
                author_id=author_id,
                notes=notes
            )

            await self.db.commit()
            await self.db.refresh(version)

            logger.info(f"Updated version status: {version_id} -> {status}")
            return version

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update version status: {e}")
            raise StrategyError(f"Status update failed: {e}") from e

    async def compare_versions(
        self,
        version1_id: UUID,
        version2_id: UUID,
        detailed: bool = True
    ) -> StrategyComparisonResult:
        """
        Compare two strategy versions

        Args:
            version1_id: ID of the first version
            version2_id: ID of the second version
            detailed: Whether to include detailed comparison

        Returns:
            Comparison result
        """
        # Get versions
        version1 = await self.get_version(version1_id)
        version2 = await self.get_version(version2_id)

        # Compare configurations
        config1 = version1.config
        config2 = version2.config

        # Calculate differences
        differences = self._calculate_differences(config1, config2)

        # Generate diff text
        diff_text = self._generate_diff_text(config1, config2) if detailed else None

        # Create comparison result
        result = StrategyComparisonResult(
            version1_id=version1_id,
            version2_id=version2_id,
            version1_number=version1.version_number,
            version2_number=version2.version_number,
            timestamp=datetime.utcnow(),
            has_changes=len(differences) > 0,
            differences=differences,
            diff_text=diff_text,
            summary=f"{len(differences)} changes found"
        )

        return result

    async def rollback_to_version(
        self,
        strategy_id: UUID,
        target_version_id: UUID,
        author_id: Optional[UUID] = None,
        reason: Optional[str] = None
    ) -> StrategyVersion:
        """
        Rollback strategy to a previous version

        Args:
            strategy_id: ID of the strategy
            target_version_id: ID of the version to rollback to
            author_id: ID of the author performing rollback
            reason: Optional reason for rollback

        Returns:
            New version created from rollback
        """
        try:
            # Get target version
            target_version = await self.get_version(target_version_id)

            if target_version.strategy_id != strategy_id:
                raise StrategyValidationError(
                    f"Version {target_version_id} does not belong to strategy {strategy_id}"
                )

            # Get current version
            current_version = await self.get_latest_version(strategy_id)
            current_config = current_version.config if current_version else {}

            # Create rollback version
            rollback_version = await self.create_version(
                strategy_id=strategy_id,
                config=target_version.config.copy(),
                description=f"Rollback to v{target_version.version_number}",
                status=VersionStatus.DRAFT,
                author_id=author_id,
                change_type=ChangeType.ROLLBACK,
                parent_version_id=target_version_id
            )

            # Add rollback metadata
            rollback_version.metadata = {
                "rollback_from_version": current_version.version_number if current_version else None,
                "rollback_to_version": target_version.version_number,
                "rollback_reason": reason,
                "rollback_timestamp": datetime.utcnow().isoformat()
            }

            await self.db.commit()

            logger.info(f"Rolled back strategy {strategy_id} to version {target_version.version_number}")
            return rollback_version

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to rollback strategy: {e}")
            raise StrategyError(f"Rollback failed: {e}") from e

    async def get_change_history(
        self,
        strategy_id: UUID,
        version_id: Optional[UUID] = None,
        change_type: Optional[ChangeType] = None,
        author_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[StrategyChangeLog]:
        """
        Get change history for a strategy

        Args:
            strategy_id: ID of the strategy
            version_id: Optional version ID filter
            change_type: Optional change type filter
            author_id: Optional author filter
            limit: Maximum number of entries to return

        Returns:
            List of change log entries
        """
        query = select(StrategyChangeLog).where(
            StrategyChangeLog.strategy_id == strategy_id
        )

        # Apply filters
        if version_id:
            query = query.where(StrategyChangeLog.version_id == version_id)

        if change_type:
            query = query.where(StrategyChangeLog.change_type == change_type)

        if author_id:
            query = query.where(StrategyChangeLog.author_id == author_id)

        # Order by timestamp (newest first) and limit
        query = query.order_by(desc(StrategyChangeLog.timestamp)).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def branch_version(
        self,
        source_version_id: UUID,
        new_version_number: str,
        description: Optional[str] = None,
        author_id: Optional[UUID] = None
    ) -> StrategyVersion:
        """
        Create a new branch from an existing version

        Args:
            source_version_id: ID of the source version
            new_version_number: Version number for the new branch
            description: Optional description
            author_id: ID of the author

        Returns:
            New branched version
        """
        try:
            # Get source version
            source_version = await self.get_version(source_version_id)

            # Create branch
            branch_version = await self.create_version(
                strategy_id=source_version.strategy_id,
                config=source_version.config.copy(),
                version_number=new_version_number,
                description=description or f"Branch from v{source_version.version_number}",
                status=VersionStatus.DRAFT,
                author_id=author_id,
                change_type=ChangeType.CREATE,
                parent_version_id=source_version_id
            )

            # Add branch metadata
            branch_version.metadata = {
                "branched_from": source_version.version_number,
                "branch_timestamp": datetime.utcnow().isoformat()
            }

            await self.db.commit()

            logger.info(f"Created branch: {new_version_number} from {source_version.version_number}")
            return branch_version

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create branch: {e}")
            raise StrategyError(f"Branch creation failed: {e}") from e

    async def merge_versions(
        self,
        strategy_id: UUID,
        source_version_id: UUID,
        target_version_id: UUID,
        merge_config: Dict[str, Any],
        author_id: Optional[UUID] = None
    ) -> StrategyVersion:
        """
        Merge two versions into a new version

        Args:
            strategy_id: ID of the strategy
            source_version_id: ID of the source version
            target_version_id: ID of the target version
            merge_config: Merged configuration
            author_id: ID of the author

        Returns:
            New merged version
        """
        try:
            # Get versions
            source_version = await self.get_version(source_version_id)
            target_version = await self.get_version(target_version_id)

            # Validate both versions belong to the same strategy
            if (source_version.strategy_id != strategy_id or
                target_version.strategy_id != strategy_id):
                raise StrategyValidationError("Versions must belong to the same strategy")

            # Generate new version number
            new_version_number = await self._generate_version_number(strategy_id)

            # Create merge version
            merge_version = await self.create_version(
                strategy_id=strategy_id,
                config=merge_config,
                version_number=new_version_number,
                description=f"Merge of v{source_version.version_number} and v{target_version.version_number}",
                status=VersionStatus.DRAFT,
                author_id=author_id,
                change_type=ChangeType.UPDATE
            )

            # Add merge metadata
            merge_version.metadata = {
                "merge_sources": [
                    source_version.version_number,
                    target_version.version_number
                ],
                "merge_timestamp": datetime.utcnow().isoformat()
            }

            await self.db.commit()

            logger.info(f"Merged versions: {source_version.version_number} + {target_version.version_number} -> {new_version_number}")
            return merge_version

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to merge versions: {e}")
            raise StrategyError(f"Version merge failed: {e}") from e

    async def _generate_version_number(self, strategy_id: UUID) -> str:
        """Generate next version number for strategy"""
        # Get latest version number
        latest = await self.get_latest_version(strategy_id)

        if not latest:
            return "1.0.0"

        # Parse and increment version number
        try:
            parts = latest.version_number.split('.')
            if len(parts) == 3:
                major, minor, patch = parts
                patch = str(int(patch) + 1)
                return f"{major}.{minor}.{patch}"
        except (ValueError, IndexError):
            pass

        # Fallback: append .1 to version number
        return f"{latest.version_number}.1"

    async def _get_current_config(self, strategy_id: UUID) -> Dict[str, Any]:
        """Get current strategy configuration"""
        strategy = await self.db.get(Strategy, strategy_id)
        if strategy and strategy.config:
            return strategy.config
        return {}

    def _calculate_changes(
        self,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
        change_type: ChangeType
    ) -> Dict[str, Any]:
        """Calculate changes between configurations"""
        changes = {
            "change_type": change_type.value,
            "timestamp": datetime.utcnow().isoformat()
        }

        if change_type in [ChangeType.CREATE, ChangeType.DELETE]:
            return changes

        # For updates, calculate specific changes
        added_keys = set(new_config.keys()) - set(old_config.keys())
        removed_keys = set(old_config.keys()) - set(new_config.keys())
        modified_keys = set()

        for key in old_config:
            if key in new_config and old_config[key] != new_config[key]:
                modified_keys.add(key)

        changes["details"] = {
            "added": {k: new_config[k] for k in added_keys},
            "removed": {k: old_config[k] for k in removed_keys},
            "modified": {
                k: {
                    "old": old_config[k],
                    "new": new_config[k]
                } for k in modified_keys
            }
        }

        return changes

    def _calculate_differences(
        self,
        config1: Dict[str, Any],
        config2: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Calculate detailed differences between two configurations"""
        differences = []

        # Check for added keys
        for key in config2:
            if key not in config1:
                differences.append({
                    "type": "added",
                    "key": key,
                    "value": config2[key]
                })

        # Check for removed keys
        for key in config1:
            if key not in config2:
                differences.append({
                    "type": "removed",
                    "key": key,
                    "value": config1[key]
                })

        # Check for modified keys
        for key in config1:
            if key in config2 and config1[key] != config2[key]:
                differences.append({
                    "type": "modified",
                    "key": key,
                    "old_value": config1[key],
                    "new_value": config2[key]
                })

        return differences

    def _generate_diff_text(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> str:
        """Generate unified diff text for configurations"""
        json1 = json.dumps(config1, indent=2, sort_keys=True).splitlines(keepends=True)
        json2 = json.dumps(config2, indent=2, sort_keys=True).splitlines(keepends=True)

        diff = difflib.unified_diff(
            json1,
            json2,
            fromfile="version1",
            tofile="version2",
            lineterm=""
        )

        return "".join(diff)

    def _is_valid_status_transition(self, old_status: VersionStatus, new_status: VersionStatus) -> bool:
        """Check if status transition is valid"""
        valid_transitions = {
            VersionStatus.DRAFT: [VersionStatus.REVIEW, VersionStatus.APPROVED, VersionStatus.DEPRECATED],
            VersionStatus.REVIEW: [VersionStatus.DRAFT, VersionStatus.APPROVED, VersionStatus.DEPRECATED],
            VersionStatus.APPROVED: [VersionStatus.PUBLISHED, VersionStatus.DEPRECATED, VersionStatus.REVIEW],
            VersionStatus.PUBLISHED: [VersionStatus.DEPRECATED, VersionStatus.ARCHIVED],
            VersionStatus.DEPRECATED: [VersionStatus.ARCHIVED, VersionStatus.DRAFT],
            VersionStatus.ARCHIVED: []  # No transitions from archived
        }

        return new_status in valid_transitions.get(old_status, [])

    async def _create_change_log(
        self,
        strategy_id: UUID,
        version_id: Optional[UUID],
        change_type: ChangeType,
        description: Optional[str],
        author_id: Optional[UUID],
        changes: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> None:
        """Create change log entry"""
        change_log = StrategyChangeLog(
            id=uuid4(),
            strategy_id=strategy_id,
            version_id=version_id,
            change_type=change_type,
            description=description or f"{change_type.value} operation",
            changes=changes or {},
            notes=notes,
            author_id=author_id,
            timestamp=datetime.utcnow()
        )

        self.db.add(change_log)

    async def get_version_tree(self, strategy_id: UUID) -> Dict[str, Any]:
        """
        Get version tree showing relationships between versions

        Args:
            strategy_id: ID of the strategy

        Returns:
            Version tree structure
        """
        versions = await self.list_versions(strategy_id, include_deprecated=True)

        # Build tree structure
        tree = {
            "strategy_id": strategy_id,
            "versions": {},
            "relationships": []
        }

        # Map versions by ID
        version_map = {}
        for version in versions:
            version_info = {
                "id": str(version.id),
                "version_number": version.version_number,
                "status": version.status,
                "created_at": version.created_at.isoformat(),
                "parent_id": str(version.parent_version_id) if version.parent_version_id else None,
                "children": []
            }
            version_map[str(version.id)] = version_info
            tree["versions"][str(version.id)] = version_info

        # Build relationships
        for version in versions:
            version_id = str(version.id)
            if version.parent_version_id:
                parent_id = str(version.parent_version_id)
                if parent_id in version_map:
                    version_map[parent_id]["children"].append(version_id)
                    tree["relationships"].append({
                        "parent": parent_id,
                        "child": version_id,
                        "type": "branch"
                    })

        return tree