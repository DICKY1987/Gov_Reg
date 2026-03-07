"""
Direct OpenAI/Anthropic API Integration for ACMS

Alternative AI adapter using direct API calls instead of CLI.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from src.acms.ai_adapter import AIAdapter, AIRequest, AIResponse


class OpenAIAdapter(AIAdapter):
    """Adapter for OpenAI API"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("OpenAI API key required (set OPENAI_API_KEY env var)")

        try:
            import openai

            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package required: pip install openai")

    def analyze_gaps(self, request: AIRequest) -> AIResponse:
        """Execute gap analysis via OpenAI API"""
        start_time = time.time()

        try:
            # Load prompt template
            with open(request.prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = json.load(f)

            # Build system and user messages
            system_message = self._build_system_message(prompt_template)
            user_message = self._build_gap_analysis_message(
                request.context, request.repo_root
            )

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            # Parse response
            content = response.choices[0].message.content
            gap_report = json.loads(content)

            return AIResponse(
                success=True,
                output=gap_report,
                execution_time_seconds=time.time() - start_time,
                metadata={"model": self.model, "tokens": response.usage.total_tokens},
            )

        except Exception as e:
            return AIResponse(
                success=False,
                error=str(e),
                execution_time_seconds=time.time() - start_time,
            )

    def generate_plan(self, request: AIRequest) -> AIResponse:
        """Generate phase plan via OpenAI API"""
        start_time = time.time()

        try:
            # Similar to analyze_gaps but for plan generation
            with open(request.prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = json.load(f)

            system_message = self._build_system_message(prompt_template)
            user_message = self._build_plan_generation_message(request.context)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            phase_plan = json.loads(content)

            return AIResponse(
                success=True,
                output=phase_plan,
                execution_time_seconds=time.time() - start_time,
                metadata={"model": self.model, "tokens": response.usage.total_tokens},
            )

        except Exception as e:
            return AIResponse(
                success=False,
                error=str(e),
                execution_time_seconds=time.time() - start_time,
            )

    def _build_system_message(self, template: Dict[str, Any]) -> str:
        """Build system message from template"""
        parts = []

        if "role" in template:
            parts.append(template["role"])

        if "instructions" in template:
            inst = template["instructions"]
            if isinstance(inst, str):
                parts.append(inst)
            elif isinstance(inst, dict):
                parts.append(json.dumps(inst, indent=2))

        parts.append(
            "\nYou MUST respond with valid JSON only. No markdown, no explanations."
        )

        return "\n\n".join(parts)

    def _build_gap_analysis_message(
        self, context: Dict[str, Any], repo_root: Path
    ) -> str:
        """Build user message for gap analysis"""
        return f"""Analyze the repository at: {repo_root}

Context: {json.dumps(context, indent=2)}

Provide a gap analysis report in the following JSON format:
{{
  "version": "1.0",
  "generated_at": "ISO timestamp",
  "gaps": [
    {{
      "gap_id": "unique_id",
      "title": "short title",
      "description": "detailed description",
      "category": "category name",
      "severity": "critical|high|medium|low|info",
      "file_paths": ["file1.py", "file2.py"],
      "dependencies": []
    }}
  ]
}}

Focus on realistic gaps: missing tests, incomplete documentation, code quality issues, etc."""

    def _build_plan_generation_message(self, context: Dict[str, Any]) -> str:
        """Build user message for plan generation"""
        return f"""Generate a phase plan for the following workstreams:

{json.dumps(context, indent=2)}

Provide a phase plan in the following JSON format:
{{
  "version": "1.0",
  "steps": [
    {{
      "step_id": "unique_id",
      "title": "step title",
      "description": "what to do",
      "type": "analysis|implementation|test|refactor"
    }}
  ]
}}"""


class AnthropicAdapter(AIAdapter):
    """Adapter for Anthropic Claude API"""

    def __init__(
        self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required (set ANTHROPIC_API_KEY env var)"
            )

        try:
            import anthropic

            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package required: pip install anthropic")

    def analyze_gaps(self, request: AIRequest) -> AIResponse:
        """Execute gap analysis via Anthropic API"""
        start_time = time.time()

        try:
            # Load prompt template
            with open(request.prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = json.load(f)

            # Build prompt
            system_message = self._build_system_message(prompt_template)
            user_message = self._build_gap_analysis_message(
                request.context, request.repo_root
            )

            # Call Anthropic API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_message,
                messages=[{"role": "user", "content": user_message}],
            )

            # Parse response
            content = message.content[0].text
            # Extract JSON from response (Claude may add explanation)
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
            else:
                json_str = content

            gap_report = json.loads(json_str)

            return AIResponse(
                success=True,
                output=gap_report,
                execution_time_seconds=time.time() - start_time,
                metadata={"model": self.model, "tokens": message.usage.output_tokens},
            )

        except Exception as e:
            return AIResponse(
                success=False,
                error=str(e),
                execution_time_seconds=time.time() - start_time,
            )

    def generate_plan(self, request: AIRequest) -> AIResponse:
        """Generate phase plan via Anthropic API"""
        # Similar implementation to analyze_gaps
        start_time = time.time()

        try:
            with open(request.prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = json.load(f)

            system_message = self._build_system_message(prompt_template)
            user_message = self._build_plan_generation_message(request.context)

            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_message,
                messages=[{"role": "user", "content": user_message}],
            )

            content = message.content[0].text
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
            else:
                json_str = content

            phase_plan = json.loads(json_str)

            return AIResponse(
                success=True,
                output=phase_plan,
                execution_time_seconds=time.time() - start_time,
                metadata={"model": self.model, "tokens": message.usage.output_tokens},
            )

        except Exception as e:
            return AIResponse(
                success=False,
                error=str(e),
                execution_time_seconds=time.time() - start_time,
            )

    def _build_system_message(self, template: Dict[str, Any]) -> str:
        """Build system message from template"""
        parts = []

        if "role" in template:
            parts.append(template["role"])

        if "instructions" in template:
            inst = template["instructions"]
            if isinstance(inst, str):
                parts.append(inst)
            elif isinstance(inst, dict):
                parts.append(json.dumps(inst, indent=2))

        parts.append(
            "\nRespond ONLY with valid JSON. No markdown code blocks, no explanations."
        )

        return "\n\n".join(parts)

    def _build_gap_analysis_message(
        self, context: Dict[str, Any], repo_root: Path
    ) -> str:
        """Build user message for gap analysis"""
        return f"""Analyze the repository at: {repo_root}

Context: {json.dumps(context, indent=2)}

Provide gap analysis in JSON format with this structure:
{{
  "version": "1.0",
  "generated_at": "ISO timestamp",
  "gaps": [array of gap objects with gap_id, title, description, category, severity, file_paths, dependencies]
}}

Focus on: missing tests, documentation gaps, code quality, error handling, configuration issues."""

    def _build_plan_generation_message(self, context: Dict[str, Any]) -> str:
        """Build user message for plan generation"""
        return f"""Generate phase plan for these workstreams:

{json.dumps(context, indent=2)}

Respond with JSON: {{"version": "1.0", "steps": [array of step objects with step_id, title, description, type]}}"""
