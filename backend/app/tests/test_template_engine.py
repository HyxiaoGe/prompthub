import pytest

from app.core.exceptions import TemplateRenderError, ValidationError
from app.services.template_engine import render_prompt, render_template, validate_variables


class TestValidateVariables:
    def test_basic_merge_with_defaults(self) -> None:
        defs = [
            {"name": "greeting", "required": False, "default": "Hello"},
            {"name": "name", "required": True},
        ]
        result = validate_variables(defs, {"name": "Alice"})
        assert result == {"greeting": "Hello", "name": "Alice"}

    def test_missing_required_raises(self) -> None:
        defs = [{"name": "name", "required": True}]
        with pytest.raises(ValidationError, match="Missing required"):
            validate_variables(defs, {})

    def test_optional_with_default(self) -> None:
        defs = [{"name": "color", "required": False, "default": "blue"}]
        result = validate_variables(defs, {})
        assert result["color"] == "blue"

    def test_enum_valid_value(self) -> None:
        defs = [{"name": "style", "required": True, "enum_values": ["formal", "casual"]}]
        result = validate_variables(defs, {"style": "formal"})
        assert result["style"] == "formal"

    def test_enum_invalid_value_raises(self) -> None:
        defs = [{"name": "style", "required": True, "enum_values": ["formal", "casual"]}]
        with pytest.raises(ValidationError, match="Invalid variable value"):
            validate_variables(defs, {"style": "weird"})


class TestRenderTemplate:
    def test_basic_render(self) -> None:
        result = render_template("Hello {{ name }}!", {"name": "World"})
        assert result == "Hello World!"

    def test_empty_template(self) -> None:
        result = render_template("", {})
        assert result == ""

    def test_no_variables_template(self) -> None:
        result = render_template("Static text", {})
        assert result == "Static text"

    def test_jinja2_loop(self) -> None:
        template = "{% for item in items %}{{ item }} {% endfor %}"
        result = render_template(template, {"items": ["a", "b", "c"]})
        assert result == "a b c "

    def test_jinja2_conditional(self) -> None:
        template = "{% if show %}visible{% else %}hidden{% endif %}"
        assert render_template(template, {"show": True}) == "visible"
        assert render_template(template, {"show": False}) == "hidden"

    def test_undefined_variable_raises(self) -> None:
        with pytest.raises(TemplateRenderError, match="Template rendering failed"):
            render_template("Hello {{ missing }}", {})

    def test_sandbox_blocks_unsafe(self) -> None:
        # Attempting to access dunder attributes should be blocked
        with pytest.raises(TemplateRenderError):
            render_template("{{ ''.__class__.__mro__[1].__subclasses__() }}", {})


    def test_enum_bool_true_matches_lowercase(self) -> None:
        defs = [{"name": "flag", "required": True, "enum_values": ["true", "false"]}]
        result = validate_variables(defs, {"flag": True})
        assert result["flag"] is True

    def test_enum_bool_false_matches_lowercase(self) -> None:
        defs = [{"name": "flag", "required": True, "enum_values": ["true", "false"]}]
        result = validate_variables(defs, {"flag": False})
        assert result["flag"] is False


class TestRenderPrompt:
    def test_full_pipeline(self) -> None:
        content = "Hello {{ name }}, style: {{ style }}"
        defs = [
            {"name": "name", "required": True},
            {"name": "style", "required": False, "default": "formal"},
        ]
        result = render_prompt(content, defs, {"name": "Alice"})
        assert result == "Hello Alice, style: formal"

    def test_provided_overrides_default(self) -> None:
        content = "Style: {{ style }}"
        defs = [{"name": "style", "required": False, "default": "formal"}]
        result = render_prompt(content, defs, {"style": "casual"})
        assert result == "Style: casual"
