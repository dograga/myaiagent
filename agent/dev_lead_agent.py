"""
Dev Lead Agent - Reviews code changes made by the Developer Agent
"""
from typing import Dict, Any, List
from langchain_google_vertexai import VertexAI
import os
import json


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
            f"- {action.get('action', 'unknown')}: {action.get('action_input', '')[:100]}"
            for action in actions
        ])
        
        review_prompt = f"""You are a Senior Dev Lead reviewing code changes.

⚠️ CRITICAL: NEVER respond with just "I understand" or simple acknowledgments.
ALWAYS provide a comprehensive, detailed review with specific feedback.

TASK REQUESTED:
{task}

ACTIONS TAKEN BY DEVELOPER:
{actions_summary}

RESULT:
{result}

REVIEW CRITERIA:
1. Does the code solve the requested task?
2. Is the code well-structured and readable?
3. Are there any potential bugs or issues?
4. Does it follow best practices?
5. Are there security concerns?
6. Is error handling adequate?

REQUIRED: Provide a comprehensive review with:
- Decision: APPROVED, NEEDS_IMPROVEMENT, or REJECTED
- Summary: Detailed summary explaining your review decision (minimum 2-3 sentences)
- Comments: Specific positive comments about what was done well (if approved)
- Issues: Detailed list of issues found with explanations (if needs improvement or rejected)
- Suggestions: Actionable suggestions for improvement with reasoning (if needs improvement)

Format your response as:
Decision: [APPROVED/NEEDS_IMPROVEMENT/REJECTED]
Summary: [Provide a detailed summary of at least 2-3 sentences explaining your decision, what the developer did well, and any concerns]
Comments: [Specific comment 1 with details], [Specific comment 2 with details]
Issues: [Detailed issue 1 with explanation], [Detailed issue 2 with explanation]
Suggestions: [Actionable suggestion 1 with reasoning], [Actionable suggestion 2 with reasoning]

EXAMPLE GOOD REVIEW:
Decision: APPROVED
Summary: The developer successfully implemented the requested feature by creating a well-structured Python module with proper error handling. The code follows PEP 8 style guidelines and includes appropriate docstrings. The implementation is clean and maintainable.
Comments: Excellent use of type hints for better code clarity, Good separation of concerns with dedicated functions, Proper error handling with try-except blocks
Issues: None
Suggestions: Consider adding unit tests for the new functions, Could add logging for better debugging in production
"""
        
        try:
            # Get review from LLM
            response = self.llm.invoke(review_prompt)
            
            # Parse the response
            decision = "approved"
            summary = response
            comments = []
            issues = []
            suggestions = []
            
            # Simple parsing
            if "APPROVED" in response.upper():
                decision = "approved"
            elif "NEEDS_IMPROVEMENT" in response.upper() or "NEEDS IMPROVEMENT" in response.upper():
                decision = "needs_improvement"
            elif "REJECTED" in response.upper():
                decision = "rejected"
            
            # Extract sections
            lines = response.split('\n')
            for line in lines:
                if line.startswith('Summary:'):
                    summary = line.replace('Summary:', '').strip()
                elif line.startswith('Comments:'):
                    comments_str = line.replace('Comments:', '').strip()
                    comments = [c.strip() for c in comments_str.split(',') if c.strip()]
                elif line.startswith('Issues:'):
                    issues_str = line.replace('Issues:', '').strip()
                    issues = [i.strip() for i in issues_str.split(',') if i.strip()]
                elif line.startswith('Suggestions:'):
                    suggestions_str = line.replace('Suggestions:', '').strip()
                    suggestions = [s.strip() for s in suggestions_str.split(',') if s.strip()]
            
            return {
                "status": "success",
                "review": summary,
                "decision": decision,
                "comments": comments,
                "issues": issues,
                "suggestions": suggestions
            }
        except Exception as e:
            return {
                "status": "error",
                "review": f"Review failed: {str(e)}",
                "decision": "error",
                "comments": [],
                "issues": [str(e)],
                "suggestions": []
            }
