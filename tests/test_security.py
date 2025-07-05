import os
import sys
import tempfile
import pytest

os.environ.setdefault('SECRET_KEY', 'test-secret')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app import sanitize_input


def test_sanitize_input_strips_tags():
    malicious = "<script>alert('hack')</script> Hello"
    assert sanitize_input(malicious) == "alert('hack') Hello"

