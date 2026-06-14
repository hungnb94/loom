"""Shared Jinja2 environment for template rendering and syntax validation."""

from jinja2 import Environment, BaseLoader

JINJA_ENV = Environment(loader=BaseLoader(), autoescape=False)
