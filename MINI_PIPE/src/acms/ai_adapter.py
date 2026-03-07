"""
AI Integration Adapter for ACMS

Provides adapters for integrating AI services into the ACMS pipeline.
Supports Phase 1 (gap analysis) and Phase 3 (plan generation).
"""

import json
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class AIRequest:
    """AI service request"""

    prompt_template_path: Path
    context: Dict[str, Any]
    repo_root: Path
    timeout_seconds: int = 300


@dataclass
class AIResponse:
    """AI service response"""

    success: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    metadata: Dict[str, Any] = None


class AIAdapter(ABC):
    """Base adapter for AI services"""

    @abstractmethod
    def analyze_gaps(self, request: AIRequest) -> AIResponse:
        """Execute gap analysis using AI"""
        pass

    @abstractmethod
    def generate_plan(self, request: AIRequest) -> AIResponse:
        """Generate phase plan using AI"""
        pass


class CopilotCLIAdapter(AIAdapter):
    """Adapter for GitHub Copilot CLI"""

    def __init__(self, copilot_binary: str = "gh copilot"):
        self.copilot_binary = copilot_binary

    def analyze_gaps(self, request: AIRequest) -> AIResponse:
        """Execute gap analysis via Copilot CLI"""
        start_time = time.time()

        try:
            # Load prompt template
            with open(request.prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = json.load(f)

            # Build prompt with context
            prompt = self._build_gap_analysis_prompt(
                prompt_template, request.context, request.repo_root
            )

            # Execute via Copilot CLI
            result = self._execute_copilot(prompt, request.timeout_seconds)

            if result["success"]:
                # Parse response to extract gap report
                gap_report = self._parse_gap_analysis_response(result["output"])

                return AIResponse(
                    success=True,
                    output=gap_report,
                    execution_time_seconds=time.time() - start_time,
                )
            else:
                return AIResponse(
                    success=False,
                    error=result["error"],
                    execution_time_seconds=time.time() - start_time,
                )

        except Exception as e:
            return AIResponse(
                success=False,
                error=str(e),
                execution_time_seconds=time.time() - start_time,
            )

    def generate_plan(self, request: AIRequest) -> AIResponse:
        """Generate phase plan via Copilot CLI"""
        start_time = time.time()

        try:
            # Load prompt template
            with open(request.prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = json.load(f)

            # Build prompt with context
            prompt = self._build_plan_generation_prompt(
                prompt_template, request.context, request.repo_root
            )

            # Execute via Copilot CLI
            result = self._execute_copilot(prompt, request.timeout_seconds)

            if result["success"]:
                # Parse response to extract phase plan
                phase_plan = self._parse_plan_response(result["output"])

                return AIResponse(
                    success=True,
                    output=phase_plan,
                    execution_time_seconds=time.time() - start_time,
                )
            else:
                return AIResponse(
                    success=False,
                    error=result["error"],
                    execution_time_seconds=time.time() - start_time,
                )

        except Exception as e:
            return AIResponse(
                success=False,
                error=str(e),
                execution_time_seconds=time.time() - start_time,
            )

    def _build_gap_analysis_prompt(
        self, template: Dict[str, Any], context: Dict[str, Any], repo_root: Path
    ) -> str:
        """Build gap analysis prompt from template"""
        # Extract prompt sections from template
        sections = []

        # Add role/context
        if "role" in template:
            sections.append(f"Role: {template['role']}")

        # Add instructions
        if "instructions" in template:
            sections.append("Instructions:")
            sections.append(template["instructions"])

        # Add repository context
        sections.append("\nRepository Path: {}".format(repo_root))
        sections.append("Analysis Scope: Full repository")

        # Add context data
        if context:
            sections.append("\nContext:")
            sections.append(json.dumps(context, indent=2))

        # Add output format
        sections.append("\nRequired Output Format:")
        sections.append("JSON object with 'gaps' array, each gap having:")
        sections.append("- gap_id (string)")
        sections.append("- title (string)")
        sections.append("- description (string)")
        sections.append("- category (string)")
        sections.append("- severity (critical|high|medium|low|info)")
        sections.append("- file_paths (array)")
        sections.append("- dependencies (array)")

        return "\n".join(sections)

    def _build_plan_generation_prompt(
        self, template: Dict[str, Any], context: Dict[str, Any], repo_root: Path
    ) -> str:
        """Build plan generation prompt from template"""
        sections = []

        # Add role/context
        if "role" in template:
            sections.append(f"Role: {template['role']}")

        # Add instructions
        if "instructions" in template:
            sections.append("Instructions:")
            sections.append(template["instructions"])

        # Add workstream context
        if "workstreams" in context:
            sections.append("\nWorkstreams to plan:")
            sections.append(json.dumps(context["workstreams"], indent=2))

        # Add output format
        sections.append("\nRequired Output Format:")
        sections.append(
            "JSON object with 'steps' array following MASTER_SPLINTER semantics"
        )

        return "\n".join(sections)

    def _execute_copilot(self, prompt: str, timeout: int) -> Dict[str, Any]:
        """Execute prompt via Copilot CLI or other AI service"""
        # Try methods in order of preference
        methods = [
            ("GitHub Copilot CLI", self._try_gh_copilot_cli),
            ("OpenAI API", self._try_openai_api),
            ("Anthropic API", self._try_anthropic_api),
            ("Mock (fallback)", self._fallback_to_mock),
        ]

        for method_name, method_func in methods:
            try:
                result = method_func(prompt, timeout)
                if result["success"]:
                    print(f"  ✓ Using {method_name}")
                    return result
                else:
                    print(
                        f"  ⚠️  {method_name} failed: {result.get('error', 'Unknown error')}"
                    )
            except Exception as e:
                print(f"  ⚠️  {method_name} exception: {e}")
                continue

        # All methods failed
        return {
            "success": False,
            "error": "All AI methods failed, including mock fallback",
            "output": None,
        }

    def _try_gh_copilot_cli(self, prompt: str, timeout: int) -> Dict[str, Any]:
        """Try GitHub Copilot CLI"""
        result = subprocess.run(
            ["gh", "copilot", "suggest", "-t", "shell"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            return {"success": True, "output": result.stdout, "error": None}
        else:
            return {
                "success": False,
                "error": f"Exit code {result.returncode}: {result.stderr}",
                "output": None,
            }

    def _try_openai_api(self, prompt: str, timeout: int) -> Dict[str, Any]:
        """Try OpenAI API (if configured)"""
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"success": False, "error": "OPENAI_API_KEY not set", "output": None}

        try:
            import openai

            openai.api_key = api_key

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                timeout=timeout,
            )

            output = response.choices[0].message.content
            return {"success": True, "output": output, "error": None}
        except ImportError:
            return {
                "success": False,
                "error": "openai package not installed",
                "output": None,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "output": None}

    def _try_anthropic_api(self, prompt: str, timeout: int) -> Dict[str, Any]:
        """Try Anthropic Claude API (if configured)"""
        import os

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "ANTHROPIC_API_KEY not set",
                "output": None,
            }

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout,
            )

            output = response.content[0].text
            return {"success": True, "output": output, "error": None}
        except ImportError:
            return {
                "success": False,
                "error": "anthropic package not installed",
                "output": None,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "output": None}

    def _fallback_to_mock(self, prompt: str) -> Dict[str, Any]:
        """Fallback to mock when Copilot unavailable"""
        print("  → Falling back to mock adapter")
        mock = MockAIAdapter()

        # Create a dummy request
        dummy_request = AIRequest(
            prompt_template_path=Path("."),
            context={},
            repo_root=Path("."),
        )
        response = mock.analyze_gaps(dummy_request)
        if response.success:
            return {
                "success": True,
                "output": json.dumps(response.output),
                "error": None,
            }
        else:
            return {"success": False, "error": response.error, "output": None}

    def _parse_gap_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse gap analysis response from AI"""
        # Try to extract JSON from response
        # Handle cases where AI returns markdown with JSON code block
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response

        return json.loads(json_str)

    def _parse_plan_response(self, response: str) -> Dict[str, Any]:
        """Parse plan generation response from AI"""
        # Same JSON extraction logic
        return self._parse_gap_analysis_response(response)


class MockAIAdapter(AIAdapter):
    """Mock adapter for testing without AI service"""

    def analyze_gaps(self, request: AIRequest) -> AIResponse:
        """Return mock gap analysis"""
        mock_report = {
            "version": "1.0",
            "generated_at": "2025-12-06T19:33:00Z",
            "gaps": [
                {
                    "gap_id": "MOCK_GAP_001",
                    "title": "Mock gap for testing",
                    "description": "This is a placeholder gap generated by MockAIAdapter",
                    "category": "testing",
                    "severity": "low",
                    "file_paths": [],
                    "dependencies": [],
                }
            ],
        }

        return AIResponse(success=True, output=mock_report, execution_time_seconds=0.1)

    def generate_plan(self, request: AIRequest) -> AIResponse:
        """Return mock phase plan"""
        mock_plan = {
            "version": "1.0",
            "steps": [
                {
                    "step_id": "MOCK_STEP_001",
                    "title": "Mock implementation step",
                    "description": "Placeholder step from MockAIAdapter",
                    "type": "implementation",
                }
            ],
        }

        return AIResponse(success=True, output=mock_plan, execution_time_seconds=0.1)


def create_ai_adapter(adapter_type: str = "mock", **kwargs) -> AIAdapter:
    """Factory function to create AI adapters"""
    adapters = {
        "mock": MockAIAdapter,
        "copilot": CopilotCLIAdapter,
    }

    # Handle "auto" adapter type - select best available
    if adapter_type == "auto":
        # Try adapters in order of preference
        import os

        for preferred in ["openai", "anthropic", "copilot", "mock"]:
            try:
                if preferred == "openai" and not os.getenv("OPENAI_API_KEY"):
                    continue
                if preferred == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
                    continue
                if preferred in ["openai", "anthropic"]:
                    from src.acms.api_adapters import AnthropicAdapter, OpenAIAdapter

                    adapters["openai"] = OpenAIAdapter
                    adapters["anthropic"] = AnthropicAdapter
                adapter_type = preferred
                print(f"  ✓ Auto-selected '{preferred}' adapter")
                break
            except ImportError:
                continue

    # Try to import API adapters if requested
    if adapter_type in ["openai", "anthropic"]:
        try:
            from src.acms.api_adapters import AnthropicAdapter, OpenAIAdapter

            adapters["openai"] = OpenAIAdapter
            adapters["anthropic"] = AnthropicAdapter
        except ImportError as e:
            print("  ⚠️  Could not load {} adapter: {}".format(adapter_type, e))
            print("  → Falling back to mock adapter")
            adapter_type = "mock"

    adapter_class = adapters.get(adapter_type)
    if not adapter_class:
        raise ValueError(f"Unknown adapter type: {adapter_type}")

    return adapter_class(**kwargs)
