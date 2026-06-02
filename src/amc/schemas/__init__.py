"""Pydantic request/response schemas for the AMC API.

The read schemas for exams and diagnostics deliberately omit every answer-key
field (``correct_answer``, ``answer``, ``v``, ``accept``). Because the response
models cannot represent those fields, a key cannot leak into a pre-submission
response even if a handler mistakenly passes a full ORM object; the security
boundary is structural, not a runtime filter.
"""

from __future__ import annotations
