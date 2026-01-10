"""
LangGraph-based AI Generation Pipeline with LiteLLM Router
"""

import os
from typing import Dict, List, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import litellm
from datetime import datetime
import asyncio
import json

# Configure LiteLLM
litellm.set_verbose = False

class GenerationState:
    """State for the generation pipeline"""
    def __init__(self):
        self.prompt: str = ""
        self.files: Dict[str, str] = {}  # path -> content
        self.artifacts: List[Dict[str, Any]] = []
        self.feedback: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.current_step: str = "research"
        self.errors: List[str] = []

class AIRouter:
    """LiteLLM-based AI router with fallback chain"""

    def __init__(self):
        self.providers = [
            "groq/llama-3.3-70b-versatile",
            "openrouter/anthropic/claude-3.5-sonnet",
            "gemini/gemini-1.5-flash-latest",
            "ollama/llama2"  # Local fallback
        ]

    async def call(self, messages: List[Dict], model_preference: str = None) -> str:
        """Call AI with fallback chain"""
        if model_preference:
            preferred_providers = [p for p in self.providers if model_preference in p]
            providers_to_try = preferred_providers + [p for p in self.providers if p not in preferred_providers]
        else:
            providers_to_try = self.providers

        last_error = None

        for provider in providers_to_try:
            try:
                response = await litellm.acompletion(
                    model=provider,
                    messages=messages,
                    max_tokens=4096,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = str(e)
                print(f"⚠️  {provider} failed: {e}")
                continue

        raise Exception(f"All providers failed. Last error: {last_error}")

class ResearcherAgent:
    """Research agent for understanding requirements"""

    def __init__(self, router: AIRouter):
        self.router = router

    async def research(self, prompt: str) -> Dict[str, Any]:
        """Research and analyze the user prompt"""
        messages = [
            {
                "role": "system",
                "content": "You are a senior software architect. Analyze the user's request and provide a detailed technical specification."
            },
            {
                "role": "user",
                "content": f"Analyze this development request and provide a technical specification:\n\n{prompt}\n\nProvide:\n1. Project type and tech stack\n2. Key features and components\n3. Architecture overview\n4. Potential challenges\n5. Success criteria"
            }
        ]

        response = await self.router.call(messages, "claude")
        return {
            "analysis": response,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "researcher"
        }

class PlannerAgent:
    """Planning agent for project structure"""

    def __init__(self, router: AIRouter):
        self.router = router

    async def plan(self, research: Dict, prompt: str) -> Dict[str, Any]:
        """Create detailed project plan"""
        messages = [
            {
                "role": "system",
                "content": "You are a technical project manager. Create detailed implementation plans."
            },
            {
                "role": "user",
                "content": f"Based on this analysis:\n{research['analysis']}\n\nOriginal request: {prompt}\n\nCreate a detailed implementation plan including:\n1. File structure\n2. Component breakdown\n3. Implementation steps\n4. Dependencies\n5. Testing strategy"
            }
        ]

        response = await self.router.call(messages, "claude")
        return {
            "plan": response,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "planner"
        }

class CoderAgent:
    """Coding agent for implementation"""

    def __init__(self, router: AIRouter):
        self.router = router

    async def code(self, plan: Dict, existing_files: Dict[str, str] = None) -> Dict[str, Any]:
        """Generate code based on plan"""
        context = ""
        if existing_files:
            context = "\nExisting files:\n" + "\n".join([f"{path}:\n{content[:500]}..." for path, content in existing_files.items()])

        messages = [
            {
                "role": "system",
                "content": "You are an expert software developer. Write clean, well-documented code."
            },
            {
                "role": "user",
                "content": f"Implementation plan:\n{plan['plan']}\n\n{context}\n\nGenerate the complete code for this project. Return format: ```language\n[code]\n```"
            }
        ]

        response = await self.router.call(messages, "groq")
        return {
            "code": response,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "coder"
        }

class DesignerAgent:
    """Design agent for UI/UX"""

    def __init__(self, router: AIRouter):
        self.router = router

    async def design(self, plan: Dict, code: Dict) -> Dict[str, Any]:
        """Generate design specifications and assets"""
        messages = [
            {
                "role": "system",
                "content": "You are a UI/UX designer. Create beautiful, modern interface designs."
            },
            {
                "role": "user",
                "content": f"Project plan:\n{plan['plan']}\n\nGenerated code:\n{code['code']}\n\nCreate UI/UX specifications including:\n1. Layout and components\n2. Color scheme and typography\n3. User flows\n4. Responsive design\n5. Accessibility considerations"
            }
        ]

        response = await self.router.call(messages, "gemini")
        return {
            "design": response,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "designer"
        }

class ReviewerAgent:
    """Review agent for quality assurance"""

    def __init__(self, router: AIRouter):
        self.router = router

    async def review(self, code: Dict, design: Dict) -> Dict[str, Any]:
        """Review code and design quality"""
        messages = [
            {
                "role": "system",
                "content": "You are a senior code reviewer. Provide constructive feedback and quality assessment."
            },
            {
                "role": "user",
                "content": f"Review this code and design:\n\nCode:\n{code['code']}\n\nDesign:\n{design['design']}\n\nProvide:\n1. Code quality assessment\n2. Security review\n3. Performance considerations\n4. Design feedback\n5. PASS/FAIL recommendation with reasons"
            }
        ]

        response = await self.router.call(messages)
        return {
            "review": response,
            "passed": "PASS" in response.upper(),
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "reviewer"
        }

class ExporterAgent:
    """Export agent for packaging deliverables"""

    def __init__(self, router: AIRouter):
        self.router = router

    async def export(self, code: Dict, design: Dict, review: Dict) -> Dict[str, Any]:
        """Package and export project deliverables"""
        messages = [
            {
                "role": "system",
                "content": "You are a DevOps engineer. Package projects for deployment."
            },
            {
                "role": "user",
                "content": f"Package this project for deployment:\n\nCode:\n{code['code']}\n\nDesign:\n{design['design']}\n\nReview:\n{review['review']}\n\nCreate:\n1. File structure\n2. Package.json/requirements.txt\n3. Deployment instructions\n4. README documentation"
            }
        ]

        response = await self.router.call(messages, "groq")
        return {
            "package": response,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": "exporter"
        }

class GenerationPipeline:
    """Main LangGraph-based generation pipeline"""

    def __init__(self):
        self.router = AIRouter()
        self.researcher = ResearcherAgent(self.router)
        self.planner = PlannerAgent(self.router)
        self.coder = CoderAgent(self.router)
        self.designer = DesignerAgent(self.router)
        self.reviewer = ReviewerAgent(self.router)
        self.exporter = ExporterAgent(self.router)

        # Build the graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(GenerationState)

        # Add nodes
        workflow.add_node("research", self._research_step)
        workflow.add_node("plan", self._plan_step)
        workflow.add_node("code", self._code_step)
        workflow.add_node("design", self._design_step)
        workflow.add_node("review", self._review_step)
        workflow.add_node("export", self._export_step)

        # Define flow
        workflow.set_entry_point("research")
        workflow.add_edge("research", "plan")
        workflow.add_edge("plan", "code")
        workflow.add_edge("code", "design")
        workflow.add_edge("design", "review")

        # Conditional routing based on review
        workflow.add_conditional_edges(
            "review",
            self._should_replan,
            {
                "replan": "plan",
                "export": "export"
            }
        )
        workflow.add_edge("export", END)

        return workflow.compile()

    async def _research_step(self, state: GenerationState) -> GenerationState:
        """Research step"""
        try:
            result = await self.researcher.research(state.prompt)
            state.metadata["research"] = result
            state.current_step = "plan"
        except Exception as e:
            state.errors.append(f"Research failed: {str(e)}")
        return state

    async def _plan_step(self, state: GenerationState) -> GenerationState:
        """Planning step"""
        try:
            research = state.metadata.get("research", {})
            result = await self.planner.plan(research, state.prompt)
            state.metadata["plan"] = result
            state.current_step = "code"
        except Exception as e:
            state.errors.append(f"Planning failed: {str(e)}")
        return state

    async def _code_step(self, state: GenerationState) -> GenerationState:
        """Coding step"""
        try:
            plan = state.metadata.get("plan", {})
            result = await self.coder.code(plan, state.files)
            state.metadata["code"] = result
            state.current_step = "design"
        except Exception as e:
            state.errors.append(f"Coding failed: {str(e)}")
        return state

    async def _design_step(self, state: GenerationState) -> GenerationState:
        """Design step"""
        try:
            plan = state.metadata.get("plan", {})
            code = state.metadata.get("code", {})
            result = await self.designer.design(plan, code)
            state.metadata["design"] = result
            state.current_step = "review"
        except Exception as e:
            state.errors.append(f"Design failed: {str(e)}")
        return state

    async def _review_step(self, state: GenerationState) -> GenerationState:
        """Review step"""
        try:
            code = state.metadata.get("code", {})
            design = state.metadata.get("design", {})
            result = await self.reviewer.review(code, design)
            state.metadata["review"] = result
            state.current_step = "export" if result.get("passed", False) else "plan"
        except Exception as e:
            state.errors.append(f"Review failed: {str(e)}")
        return state

    async def _export_step(self, state: GenerationState) -> GenerationState:
        """Export step"""
        try:
            code = state.metadata.get("code", {})
            design = state.metadata.get("design", {})
            review = state.metadata.get("review", {})
            result = await self.exporter.export(code, design, review)
            state.metadata["export"] = result
            state.current_step = "complete"
        except Exception as e:
            state.errors.append(f"Export failed: {str(e)}")
        return state

    def _should_replan(self, state: GenerationState) -> str:
        """Determine if we should replan or export"""
        review = state.metadata.get("review", {})
        return "export" if review.get("passed", False) else "replan"

    async def generate(self, prompt: str, existing_files: Dict[str, str] = None) -> Dict[str, Any]:
        """Run the complete generation pipeline"""
        initial_state = GenerationState()
        initial_state.prompt = prompt
        initial_state.files = existing_files or {}

        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)

            return {
                "success": len(final_state.errors) == 0,
                "artifacts": final_state.artifacts,
                "metadata": final_state.metadata,
                "errors": final_state.errors,
                "current_step": final_state.current_step
            }

        except Exception as e:
            return {
                "success": False,
                "errors": [str(e)],
                "metadata": {},
                "artifacts": []
            }

# Global pipeline instance
generation_pipeline = GenerationPipeline()