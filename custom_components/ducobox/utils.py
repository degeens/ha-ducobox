"""Utility functions for the DucoBox integration."""


def format_box_model_name(model_name: str) -> str:
    """Format a raw box model name by replacing underscores with spaces and title-casing it."""
    return model_name.replace("_", " ").title()
