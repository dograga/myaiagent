"""
Dev Lead Agent - Reviews code changes made by the Developer Agent
"""
from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, AgentOutputParser, AgentAction, AgentFinish
from langchain.tools import Tool
from langchain.schema import StringPromptValue
from langchain_core.prompt_values import PromptValue
from langchain_google_vertexai import VertexAI
from pydantic import Field, BaseModel
import os
import json


class DevLeadPromptTemplate(BaseModel):
    """Custom prompt template for Dev Lead Agent."""
    template: str = Field(description="The prompt template")
    input_variables: List[str] = Field(default_factory=list)

    def format(self, **kwargs) -> str:
        """Format the template with the given variables."""
        return self.template.format(**kwargs)
    
    def format_prompt(self, **kwargs) -> PromptValue:
        return StringPromptValue(text=self.format(**kwargs))


class DevLeadAgent:
    """Dev Lead Agent that reviews code changes."""
    
    def __init__(self):
        """Initialize the Dev Lead Agent."""
        gcp_project = os.getenv("GCP_PROJECT_ID")
        gcp_location = os.getenv("GCP_LOCATION", "us-central1")
        model_name = os.getenv("VERTEX_MODEL_NAME", "text-bison@002")
        
        if not gcp_project:
            raise ValueError("GCP_PROJECT_ID must be set in environment variables")
        
        try:
            self.llm = VertexAI(
                model_name=model_name,
                project=gcp_project,
                location=gcp_location,
                max_output_tokens=2048,
                temperature=0.3,  # Slightly higher for more nuanced reviews
                top_p=0.95,
                top_k=40,
                verbose=True
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Dev Lead Agent: {str(e)}")
        
        self.tools = self._setup_tools()
        self.agent = self._create_agent()
    
    def _setup_tools(self) -> List[Tool]:
        """Set up tools for the Dev Lead Agent."""
        return [
            Tool(
                name="approve_changes",
                func=self._approve_changes,
                description="Approve the code changes. Use this when the changes meet quality standards. Input: JSON with 'summary' and 'comments'."
            ),
            Tool(
                name="request_improvements",
                func=self._request_improvements,
                description="Request improvements to the code. Use this when changes need refinement. Input: JSON with 'issues' (list) and 'suggestions' (list)."
            ),
            Tool(
                name="reject_changes",
                func=self._reject_changes,
                description="Reject the code changes. Use this for critical issues. Input: JSON with 'reason' and 'required_fixes' (list)."
            )
        ]
    
    def _approve_changes(self, input_str: str) -> Dict[str, Any]:
        """Approve the changes."""
        try:
            data = json.loads(input_str)
            return {
                "status": "approved",
                "decision": "approved",
                "summary": data.get("summary", "Changes approved"),
                "comments": data.get("comments", [])
            }
        except json.JSONDecodeError:
            return {
                "status": "approved",
                "decision": "approved",
                "summary": input_str,
                "comments": []
            }
    
    def _request_improvements(self, input_str: str) -> Dict[str, Any]:
        """Request improvements."""
        try:
            data = json.loads(input_str)
            return {
                "status": "needs_improvement",
                "decision": "needs_improvement",
                "issues": data.get("issues", []),
                "suggestions": data.get("suggestions", [])
            }
        except json.JSONDecodeError:
            return {
                "status": "needs_improvement",
                "decision": "needs_improvement",
                "issues": [input_str],
                "suggestions": []
            }
    
    def _reject_changes(self, input_str: str) -> Dict[str, Any]:
        """Reject the changes."""
        try:
            data = json.loads(input_str)
            return {
                "status": "rejected",
                "decision": "rejected",
                "reason": data.get("reason", "Changes rejected"),
                "required_fixes": data.get("required_fixes", [])
            }
        except json.JSONDecodeError:
            return {
                "status": "rejected",
                "decision": "rejected",
                "reason": input_str,
                "required_fixes": []
            }
    
    def _create_agent(self) -> AgentExecutor:
        """Create the Dev Lead agent."""
        from langchain.agents import ZeroShotAgent
        from langchain.memory import ConversationBufferMemory
        
        template = """You are a Senior Dev Lead reviewing code changes made by a developer.

Your role is to:
1. Review the task that was requested
2. Review the actions taken by the developer
3. Check if the implementation meets requirements
4. Verify code quality, best practices, and potential issues
5. Make a decision: approve, request improvements, or reject

You have access to the following tools:
{tools}

Use this format:

Question: the review task
Thought: I need to analyze the developer's work
Action: [tool name]
Action Input: [tool input as JSON]
Observation: [result]
Thought: Based on my review...
Final Answer: [Your review summary]

REVIEW CRITERIA:
- Does the code solve the requested task?
- Is the code well-structured and readable?
- Are there any potential bugs or issues?
- Does it follow best practices?
- Are there security concerns?
- Is error handling adequate?

Begin!

Question: {input}
Developer's Task: {task}
Developer's Actions: {actions}
Developer's Result: {result}

{agent_scratchpad}"""

        prompt = DevLeadPromptTemplate(
            template=template,
            input_variables=["input", "task", "actions", "result", "agent_scratchpad", "tools", "tool_names"]
        )
        
        tools = self.tools
        tool_names = [tool.name for tool in tools]
        
        agent = ZeroShotAgent(
            llm_chain=self.llm,
            allowed_tools=tool_names
        )
        
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            verbose=True,
            memory=memory,
            max_iterations=5,
            early_stopping_method="force",
            handle_parsing_errors=True
        )
    
    def review(self, task: str, actions: List[Dict[str, Any]], result: str) -> Dict[str, Any]:
        """
        Review the developer's work.
        
        Args:
            task: The original task requested
            actions: List of actions taken by the developer
            result: The final result/output from the developer
            
        Returns:
            Review decision with feedback
        """
        # Format actions for review
        actions_summary = "\n".join([
            f"- {action.get('action', 'unknown')}: {action.get('action_input', '')}"
            for action in actions
        ])
        
        review_input = f"""
Please review the following development work:

Task: {task}
Actions Taken: {actions_summary}
Result: {result}

Provide your review and decision.
"""
        
        try:
            # Run the agent
            response = self.agent.run(
                input=review_input,
                task=task,
                actions=actions_summary,
                result=result
            )
            
            # Parse the response to extract decision
            # The agent should have used one of the tools
            return {
                "status": "success",
                "review": response,
                "decision": "approved"  # Default if not specified
            }
        except Exception as e:
            return {
                "status": "error",
                "review": f"Review failed: {str(e)}",
                "decision": "error"
            }
