from typing import List, Dict, Any
from langchain_google_vertexai import VertexAI
import os
from dotenv import load_dotenv

load_dotenv()

class ProjectManagerLeadAgent:
    """
    Project Manager Lead Agent that reviews project management tasks and Jira operations.
    """
    
    def __init__(self):
        gcp_project = os.getenv("GCP_PROJECT_ID")
        gcp_location = os.getenv("GCP_LOCATION", "us-central1")
        model_name = os.getenv("VERTEX_MODEL_NAME", "text-bison@002")
        
        if not gcp_project:
            raise RuntimeError(
                "GCP_PROJECT_ID is not set. Please configure it in your .env file."
            )
        
        self.llm = VertexAI(
            model_name=model_name,
            project=gcp_project,
            location=gcp_location,
            max_output_tokens=2048,
            temperature=0.3,
            top_p=0.95,
            top_k=40
        )
    
    def review(self, task: str, actions: List[Dict[str, Any]], result: str) -> Dict[str, Any]:
        """
        Review the project management task performed by the PM Agent.
        
        Args:
            task: The original task/query
            actions: List of actions taken by the agent
            result: The final result/answer
            
        Returns:
            Dictionary with review results
        """
        # Format actions for review
        actions_text = ""
        for i, action in enumerate(actions, 1):
            actions_text += f"\n{i}. Action: {action.get('action', 'Unknown')}"
            actions_text += f"\n   Input: {action.get('action_input', 'N/A')}"
            actions_text += f"\n   Result: {action.get('observation', 'N/A')[:200]}..."
        
        review_prompt = f"""You are a Senior Project Manager reviewing the work of a Project Manager AI assistant.

**Original Task:**
{task}

**Actions Taken:**
{actions_text}

**Final Result:**
{result}

**Review Criteria:**

1. **Data Accuracy:**
   - Was the correct Jira data retrieved?
   - Are epic/story keys properly formatted?
   - Is the status information accurate?

2. **Completeness:**
   - Did the agent answer the full question?
   - Was all requested information provided?
   - Are there any missing details?

3. **Presentation:**
   - Is the information well-organized and easy to read?
   - Are summaries clear and concise?
   - Is the format appropriate for the question?

4. **Tool Usage:**
   - Were the right Jira tools used?
   - Were tools used efficiently?
   - Were any unnecessary API calls made?

5. **Updates (if applicable):**
   - Were story updates performed correctly?
   - Were proper permissions considered?
   - Was appropriate confirmation provided?

6. **Best Practices:**
   - Did the agent follow Jira best practices?
   - Was the response professional and clear?
   - Were any risks or issues identified?

**Provide your review in this format:**

Decision: [APPROVED / NEEDS_IMPROVEMENT / REJECTED]

Summary: [Brief overall assessment]

Positive Feedback:
- [What was done well]
- [Strengths of the approach]

Issues (if any):
- [Problems or errors found]
- [Missing information]

Suggestions (if any):
- [How to improve]
- [Additional considerations]

Be constructive and specific in your feedback."""

        try:
            review_text = self.llm.predict(review_prompt)
            
            # Parse the review
            decision = "APPROVED"
            if "NEEDS_IMPROVEMENT" in review_text:
                decision = "NEEDS_IMPROVEMENT"
            elif "REJECTED" in review_text:
                decision = "REJECTED"
            
            # Extract sections
            summary = ""
            comments = []
            issues = []
            suggestions = []
            
            lines = review_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("Summary:"):
                    summary = line.replace("Summary:", "").strip()
                    current_section = "summary"
                elif line.startswith("Positive Feedback:"):
                    current_section = "comments"
                elif line.startswith("Issues"):
                    current_section = "issues"
                elif line.startswith("Suggestions"):
                    current_section = "suggestions"
                elif line.startswith("-") or line.startswith("•"):
                    item = line.lstrip("-•").strip()
                    if current_section == "comments":
                        comments.append(item)
                    elif current_section == "issues":
                        issues.append(item)
                    elif current_section == "suggestions":
                        suggestions.append(item)
            
            return {
                "status": "success",
                "decision": decision,
                "review": review_text,
                "summary": summary or "Review completed",
                "comments": comments,
                "issues": issues,
                "suggestions": suggestions
            }
        
        except Exception as e:
            return {
                "status": "error",
                "decision": "ERROR",
                "review": f"Failed to complete review: {str(e)}",
                "summary": "Review failed",
                "comments": [],
                "issues": [f"Review error: {str(e)}"],
                "suggestions": []
            }
