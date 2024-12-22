from django.db import models
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple, Type

logger = logging.getLogger(__name__)


@dataclass
class ValidationProblem:
    field_name: str
    value: Any
    field_type: str
    error: Optional[str] = None
    min_limit: Optional[int] = None
    max_limit: Optional[int] = None
    current_length: Optional[int] = None
    max_length: Optional[int] = None


class FieldValidator:
    INTEGER_FIELD_LIMITS: Dict[Type[models.Field], Tuple[int, int]] = {
        models.SmallIntegerField: (-32768, 32767),
        models.IntegerField: (-2147483648, 2147483647),
        models.BigIntegerField: (-9223372036854775808, 9223372036854775807),
        models.PositiveSmallIntegerField: (0, 32767),
        models.PositiveIntegerField: (0, 2147483647),
    }

    @staticmethod
    def convert_to_integer(value: Any) -> Tuple[Optional[int], Optional[str]]:
        """Convert a value to integer, returning (value, error_message)."""
        try:
            if isinstance(value, str):
                if "e" in value.lower() or "." in value:
                    return int(float(value)), None
                return int(value), None
            return int(value), None
        except (ValueError, TypeError) as e:
            return None, f"Could not convert to integer: {str(e)}"

    @classmethod
    def validate_integer_field(
        cls, field_name: str, value: Any, field_type: Type[models.Field]
    ) -> Optional[ValidationProblem]:
        """Validate an integer field value."""
        if value is None:
            return None

        converted_value, error = cls.convert_to_integer(value)
        if error:
            return ValidationProblem(
                field_name=field_name,
                value=value,
                field_type=field_type.__name__,
                error=error,
            )

        min_limit, max_limit = cls.INTEGER_FIELD_LIMITS[field_type]
        if converted_value < min_limit or converted_value > max_limit:
            return ValidationProblem(
                field_name=field_name,
                value=converted_value,
                field_type=field_type.__name__,
                min_limit=min_limit,
                max_limit=max_limit,
            )

        return None

    @staticmethod
    def validate_string_field(
        field_name: str, value: Any, field: models.Field
    ) -> Optional[ValidationProblem]:
        """Validate a string field value."""
        if value is None:
            return None

        str_value = str(value)
        max_length = getattr(field, "max_length", None)

        if max_length is not None and len(str_value) > max_length:
            return ValidationProblem(
                field_name=field_name,
                value=str_value,
                field_type=type(field).__name__,
                error=f"String length {len(str_value)} exceeds maximum length {max_length}",
                current_length=len(str_value),
                max_length=max_length,
            )

        return None


def debug_field_limits(model_instance: models.Model) -> List[ValidationProblem]:
    """
    Check all fields in a model instance against database limits.
    Returns a list of validation problems found.
    """
    problems = []
    validator = FieldValidator()

    for field in model_instance._meta.fields:
        field_name = field.name
        value = getattr(model_instance, field_name)

        if value is None:
            continue

        # Integer validation
        if type(field) in validator.INTEGER_FIELD_LIMITS:
            problem = validator.validate_integer_field(field_name, value, type(field))
            if problem:
                problems.append(problem)

        # String validation
        elif isinstance(field, (models.CharField, models.TextField)):
            problem = validator.validate_string_field(field_name, value, field)
            if problem:
                problems.append(problem)

    return problems


def format_validation_error(model_name: str, problems: List[ValidationProblem]) -> str:
    """Format validation problems into a readable error message."""
    error_msg = f"Field validation failed in {model_name}:"

    for p in problems:
        if p.error:
            if p.current_length is not None:  # String length error
                value_display = (
                    f"'{p.value[:50]}...'" if len(p.value) > 50 else f"'{p.value}'"
                )
                error_msg += (
                    f"\nField '{p.field_name}' ({p.field_type}): {p.error}\n"
                    f"Value: {value_display}"
                )
            else:  # Other error
                error_msg += f"\nField '{p.field_name}' ({p.field_type}): {p.error}"
        else:  # Integer range error
            error_msg += (
                f"\nField '{p.field_name}' ({p.field_type}) value {p.value} "
                f"is outside allowed range ({p.min_limit} to {p.max_limit})"
            )

    return error_msg


def check_field_limits(sender, instance, **kwargs):
    """Signal receiver that checks for potential field limit violations before saving."""
    problems = debug_field_limits(instance)
    if problems:
        error_msg = format_validation_error(instance.__class__.__name__, problems)
        logger.error(error_msg)
        raise ValueError(error_msg)
