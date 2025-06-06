"""Basic helper functions for model testing.

This module provides reusable test functions for common model properties
like inheritance, table names, and string representation.
"""


def check_model_inheritance(model_class, parent_class):
    """Test that a model inherits from the correct parent class.

    Args:
        model_class: The model class to test
        parent_class: The expected parent class
    """
    assert issubclass(model_class, parent_class)


def check_model_tablename(model_class, expected_tablename):
    """Test that a model has the correct table name.

    Args:
        model_class: The model class to test
        expected_tablename: The expected table name
    """
    assert model_class.__tablename__ == expected_tablename


def check_model_repr(model_instance, expected_attributes):
    """Test the string representation of a model instance.

    Args:
        model_instance: The model instance to test
        expected_attributes: Dict of attribute names and values expected in __repr__
    """
    repr_string = repr(model_instance)
    model_name = model_instance.__class__.__name__
    assert model_name in repr_string

    for attr_name, attr_value in expected_attributes.items():
        expected_text = f"{attr_name}={attr_value}"
        assert (
            expected_text in repr_string
        ), f"Expected '{expected_text}' in repr, got '{repr_string}'"


def check_model_columns_existence(model_class, column_names):
    """Test that a model has all the expected columns.

    Args:
        model_class: The model class to test
        column_names: List of column names that should exist
    """
    for column_name in column_names:
        assert hasattr(
            model_class, column_name
        ), f"Column '{column_name}' not found in {model_class.__name__}"


def check_model_to_dict(model_instance, expected_values):
    """Test the to_dict method of a model instance.

    Args:
        model_instance: The model instance to test
        expected_values: Dictionary of attribute names and values expected in the result
    """
    dict_data = model_instance.to_dict()

    assert isinstance(dict_data, dict)
    for key, value in expected_values.items():
        assert key in dict_data, f"Key '{key}' not found in to_dict() result"
        assert dict_data[key] == value, f"Expected {dict_data[key]} to equal {value}"
