from django.test import TestCase
from django.db import models
from django.db.models.signals import pre_save


# Test Model
class ValidationModel(models.Model):
    small_int = models.SmallIntegerField()
    regular_int = models.IntegerField()
    big_int = models.BigIntegerField()
    positive_small_int = models.PositiveSmallIntegerField()
    positive_int = models.PositiveIntegerField()
    short_text = models.CharField(max_length=5)
    long_text = models.CharField(max_length=500)
    unlimited_text = models.TextField()

    class Meta:
        # Prevent Django from creating actual DB tables
        app_label = "test_app"
        managed = False


class FieldValidatorSignalTest(TestCase):
    def setUp(self):
        # Temporarily disconnect other pre_save signals if any
        self.saved_signals = pre_save.receivers
        pre_save.receivers = []

        # Connect our signal
        from actions_insider.middleware import check_field_limits

        self.signal = pre_save.connect(check_field_limits)

    def tearDown(self):
        # Restore original signals
        pre_save.receivers = self.saved_signals

    def test_valid_integers(self):
        """Test that valid integers don't raise exceptions"""
        model = ValidationModel(
            small_int=32767,  # Max SmallIntegerField
            regular_int=2147483647,  # Max IntegerField
            big_int=9223372036854775807,  # Max BigIntegerField
            positive_small_int=32767,  # Max PositiveSmallIntegerField
            positive_int=2147483647,  # Max PositiveIntegerField
        )

        pre_save.send(sender=ValidationModel, instance=model)

    def test_small_integer_overflow(self):
        """Test SmallIntegerField overflow detection"""
        model = ValidationModel(
            small_int=32768,  # One more than max
            regular_int=0,
            big_int=0,
            positive_small_int=0,
            positive_int=0,
        )

        with self.assertRaises(ValueError) as context:
            pre_save.send(sender=ValidationModel, instance=model)

        self.assertIn("small_int", str(context.exception))
        self.assertIn("32768", str(context.exception))

    def test_regular_integer_overflow(self):
        """Test IntegerField overflow detection"""
        model = ValidationModel(
            small_int=0,
            regular_int=2147483648,  # One more than max
            big_int=0,
            positive_small_int=0,
            positive_int=0,
        )

        with self.assertRaises(ValueError) as context:
            pre_save.send(sender=ValidationModel, instance=model)

        self.assertIn("regular_int", str(context.exception))
        self.assertIn("2147483648", str(context.exception))

    def test_positive_integer_negative_value(self):
        """Test that negative values in positive fields are caught"""
        model = ValidationModel(
            small_int=0,
            regular_int=0,
            big_int=0,
            positive_small_int=-1,  # Negative value in positive field
            positive_int=0,
        )

        with self.assertRaises(ValueError) as context:
            pre_save.send(sender=ValidationModel, instance=model)

        self.assertIn("positive_small_int", str(context.exception))
        self.assertIn("-1", str(context.exception))

    def test_multiple_overflows(self):
        """Test detection of multiple overflow fields at once"""
        model = ValidationModel(
            small_int=32768,  # Overflow
            regular_int=2147483648,  # Overflow
            big_int=0,
            positive_small_int=32768,  # Overflow
            positive_int=0,
        )

        with self.assertRaises(ValueError) as context:
            pre_save.send(sender=ValidationModel, instance=model)

        error_message = str(context.exception)
        self.assertIn("small_int", error_message)
        self.assertIn("regular_int", error_message)
        self.assertIn("positive_small_int", error_message)

    def test_none_values(self):
        """Test that None values are handled correctly"""
        model = ValidationModel(
            small_int=None,
            regular_int=None,
            big_int=None,
            positive_small_int=None,
            positive_int=None,
        )

        pre_save.send(sender=ValidationModel, instance=model)

    def test_valid_string_integers(self):
        """Test that valid string integers are properly converted"""
        model = ValidationModel(
            small_int="32767",  # Max SmallIntegerField as string
            regular_int="42",  # Regular string integer
            positive_int="100",  # Positive string integer
        )

        pre_save.send(sender=ValidationModel, instance=model)

    def test_scientific_notation(self):
        """Test handling of scientific notation strings"""
        model = ValidationModel(
            small_int="1e2",  # 100
            regular_int="1.5e3",  # 1500
            positive_int="1e3",  # 1000
        )

        pre_save.send(sender=ValidationModel, instance=model)

    def test_decimal_strings(self):
        """Test handling of decimal strings"""
        model = ValidationModel(
            small_int="100.0",
            regular_int="42.5",  # Will be truncated to 42
            positive_int="10.7",  # Will be truncated to 10
        )

        pre_save.send(sender=ValidationModel, instance=model)

    def test_invalid_string_values(self):
        """Test that invalid strings are caught"""
        invalid_cases = [
            {"small_int": "not_a_number"},
            {"regular_int": "12.34.56"},
            {"positive_int": "1,000"},  # Comma is not valid
            {"regular_int": ""},  # Empty string
            {"small_int": "♠"},  # Special character
            {"positive_int": "1.2.3e4"},  # Invalid scientific notation
        ]

        for invalid_data in invalid_cases:
            field_name = list(invalid_data.keys())[0]
            model_data = {
                "small_int": "1",
                "regular_int": "1",
                "positive_int": "1",
                **invalid_data,
            }
            model = ValidationModel(**model_data)

            with self.assertRaises(ValueError) as context:
                pre_save.send(sender=ValidationModel, instance=model)

            self.assertIn(field_name, str(context.exception))
            self.assertIn("Could not convert to integer", str(context.exception))

    def test_string_overflow(self):
        """Test overflow with string values"""
        model = ValidationModel(
            small_int="32768",  # One more than SmallIntegerField max
            regular_int="1",
            positive_int="1",
        )

        with self.assertRaises(ValueError) as context:
            pre_save.send(sender=ValidationModel, instance=model)

        self.assertIn("32768", str(context.exception))
        self.assertIn("small_int", str(context.exception))

    def test_scientific_notation_overflow(self):
        """Test overflow with scientific notation"""
        model = ValidationModel(
            small_int="1e5",  # 100,000 - too big for SmallIntegerField
            regular_int="1",
            positive_int="1",
        )

        with self.assertRaises(ValueError) as context:
            pre_save.send(sender=ValidationModel, instance=model)

        self.assertIn("small_int", str(context.exception))

    def test_valid_string_lengths(self):
        """Test that valid string lengths are accepted"""
        model = ValidationModel(
            small_int=1,
            regular_int=1,
            short_text="Hello",  # Exactly 5 chars
            long_text="Test",  # Well under 500
            unlimited_text="Any length is fine here",
        )
        pre_save.send(sender=ValidationModel, instance=model)

    def test_string_length_overflow(self):
        """Test that string length limits are enforced"""
        model = ValidationModel(
            small_int=1,
            regular_int=1,
            short_text="Too long for five chars",
            long_text="A" * 501,  # One character too many
            unlimited_text="Any length is fine here",
        )

        with self.assertRaises(ValueError) as context:
            pre_save.send(sender=ValidationModel, instance=model)

        error_msg = str(context.exception)
        self.assertIn("short_text", error_msg)
        self.assertIn("length", error_msg)
        self.assertIn("5", error_msg)

    def test_non_string_values(self):
        """Test that non-string values are converted and checked"""
        model = ValidationModel(
            small_int=1,
            regular_int=1,
            short_text=12345,  # Numeric value exactly 5 digits
            long_text=123,  # Numeric value within limits
            unlimited_text=None,
        )
        pre_save.send(sender=ValidationModel, instance=model)

    def test_very_long_string_truncation_in_error(self):
        """Test that very long strings are properly truncated in error messages"""
        long_string = "A" * 1000
        model = ValidationModel(
            small_int=1,
            regular_int=1,
            short_text=long_string,
            long_text="Test",
            unlimited_text="Test",
        )

        with self.assertRaises(ValueError) as context:
            pre_save.send(sender=ValidationModel, instance=model)

        error_msg = str(context.exception)
        self.assertIn("...", error_msg)  # Check that the value was truncated
        self.assertTrue(
            len(error_msg) < 1000
        )  # Error message should be reasonable length

    def test_combined_integer_and_string_validation(self):
        """Test both integer overflow and string length validation together"""
        model = ValidationModel(
            small_int=32768,  # Too big
            regular_int=1,
            short_text="Too long for five chars",  # Too long
            long_text="Test",
            unlimited_text="Test",
        )

        with self.assertRaises(ValueError) as context:
            pre_save.send(sender=ValidationModel, instance=model)

        error_msg = str(context.exception)
        self.assertIn("small_int", error_msg)  # Should mention integer overflow
        self.assertIn("short_text", error_msg)  # Should mention string length
