"""Centralized enum definitions — the single source of truth for all
taxonomy / category values used across the platform.

When adding a new enum value, update this file and the i18n dictionary
at ``docs/i18n-enums.md`` so the frontend stays in sync.
"""

from enum import StrEnum

# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class UserRole(StrEnum):
    """User permission roles."""

    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------


class PromptFormat(StrEnum):
    """Supported prompt content formats."""

    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    CHAT = "chat"


class TemplateEngine(StrEnum):
    """Template rendering engines."""

    JINJA2 = "jinja2"
    MUSTACHE = "mustache"
    NONE = "none"


class PromptCategory(StrEnum):
    """Pre-defined prompt categories.

    If your project needs additional categories, add them here and
    update ``docs/i18n-enums.md`` so the frontend i18n mapping stays in sync.
    """

    SYSTEM = "system"
    ASSISTANT = "assistant"
    GENERATION = "generation"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    EXTRACTION = "extraction"
    REWRITE = "rewrite"
    ANALYSIS = "analysis"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"


class VariableType(StrEnum):
    """Prompt variable types."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    TEXT = "text"
    JSON = "json"


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------


class VersionStatus(StrEnum):
    """Prompt version lifecycle statuses."""

    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class BumpType(StrEnum):
    """Semantic version bump types."""

    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------


class MergeStrategy(StrEnum):
    """Scene pipeline merge strategies."""

    CONCAT = "concat"
    CHAIN = "chain"
    SELECT_BEST = "select_best"


class ConditionOperator(StrEnum):
    """Pipeline step condition operators."""

    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"


# ---------------------------------------------------------------------------
# Prompt Reference
# ---------------------------------------------------------------------------


class RefType(StrEnum):
    """Prompt cross-reference relationship types."""

    EXTENDS = "extends"
    INCLUDES = "includes"
    COMPOSES = "composes"


# ---------------------------------------------------------------------------
# AI Service
# ---------------------------------------------------------------------------


class LintSeverity(StrEnum):
    """Lint issue severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class EnhanceAspect(StrEnum):
    """Pre-defined aspects for prompt enhancement."""

    CLARITY = "clarity"
    SPECIFICITY = "specificity"
    STRUCTURE = "structure"
    CONCISENESS = "conciseness"
    TONE = "tone"


class VariantType(StrEnum):
    """Pre-defined prompt variant styles."""

    CONCISE = "concise"
    DETAILED = "detailed"
    CREATIVE = "creative"
    FORMAL = "formal"
    CASUAL = "casual"


class EvaluateCriterion(StrEnum):
    """Pre-defined prompt evaluation criteria."""

    CLARITY = "clarity"
    SPECIFICITY = "specificity"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    RELEVANCE = "relevance"


# ---------------------------------------------------------------------------
# Pagination / Query
# ---------------------------------------------------------------------------


class SortOrder(StrEnum):
    """Sort direction for list queries."""

    ASC = "asc"
    DESC = "desc"
