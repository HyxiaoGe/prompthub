from typing import Any

from jinja2 import StrictUndefined, TemplateSyntaxError, UndefinedError
from jinja2.sandbox import SandboxedEnvironment, SecurityError

from app.core.exceptions import TemplateRenderError, ValidationError

_sandbox_env = SandboxedEnvironment(
    autoescape=False,
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)


def validate_variables(
    variable_definitions: list[dict],
    provided_variables: dict[str, Any],
) -> dict[str, Any]:
    """Validate provided variables against definitions, merge with defaults."""
    defaults: dict[str, Any] = {}
    required_names: set[str] = set()
    enum_map: dict[str, list[str]] = {}

    for defn in variable_definitions:
        name = defn.get("name", "")
        if defn.get("default") is not None:
            defaults[name] = defn["default"]
        if defn.get("required", True):
            required_names.add(name)
        if defn.get("enum_values"):
            enum_map[name] = defn["enum_values"]

    result = {**defaults, **provided_variables}

    # Check required
    missing = required_names - set(result.keys())
    if missing:
        raise ValidationError(
            message="Missing required variables",
            detail=f"Missing: {', '.join(sorted(missing))}",
        )

    # Check enums
    for name, allowed in enum_map.items():
        if name in result:
            val = result[name]
            val_str = str(val).lower() if isinstance(val, bool) else str(val)
            if val_str not in allowed:
                raise ValidationError(
                    message="Invalid variable value",
                    detail=f"Variable '{name}' must be one of {allowed}, got '{result[name]}'",
                )

    return result


def render_template(content: str, variables: dict[str, Any]) -> str:
    """Render a Jinja2 template in a sandboxed environment."""
    try:
        template = _sandbox_env.from_string(content)
        return template.render(**variables)
    except TemplateSyntaxError as e:
        raise TemplateRenderError(
            detail=f"Template syntax error: {e.message}",
        )
    except UndefinedError as e:
        raise TemplateRenderError(
            detail=f"Undefined variable: {e.message}",
        )
    except SecurityError as e:
        raise TemplateRenderError(
            detail=f"Unsafe operation blocked: {e}",
        )


def render_prompt(
    content: str,
    variable_definitions: list[dict],
    provided_variables: dict[str, Any],
) -> str:
    """High-level: validate variables then render template."""
    merged = validate_variables(variable_definitions, provided_variables)
    return render_template(content, merged)
