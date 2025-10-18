"""
DevOps Lead Agent - Reviews DevOps configurations and changes made by the DevOps Agent
"""
from typing import Dict, Any, List
from langchain_google_vertexai import VertexAI
import os
import json


class DevOpsLeadAgent:
    """DevOps Lead Agent that reviews infrastructure and CI/CD configurations."""
    
    def __init__(self):
        """Initialize the DevOps Lead Agent."""
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
            raise RuntimeError(f"Failed to initialize DevOps Lead Agent: {str(e)}")
    
    def review(self, task: str, actions: List[Dict[str, Any]], result: str) -> Dict[str, Any]:
        """
        Review the DevOps engineer's work.
        
        Args:
            task: The original task requested
            actions: List of actions taken by the DevOps agent
            result: The final result/output from the DevOps agent
            
        Returns:
            Review decision with feedback
        """
        # Format actions for review
        actions_summary = "\n".join([
            f"- {action.get('action', 'unknown')}: {action.get('action_input', '')[:100]}"
            for action in actions
        ])
        
        review_prompt = f"""You are a Senior DevOps Lead reviewing infrastructure and CI/CD configurations.

TASK REQUESTED:
{task}

ACTIONS TAKEN BY DEVOPS ENGINEER:
{actions_summary}

RESULT:
{result}

REVIEW CRITERIA:
1. **Infrastructure as Code (Terraform)**:
   - Are resources properly defined with required attributes?
   - Are security best practices followed (security groups, IAM roles)?
   - Are variables and outputs properly used?
   - Is the state management configured correctly?
   - Are there any cost optimization opportunities?

2. **Kubernetes Configurations**:
   - Are resource limits and requests properly set?
   - Are health checks (liveness/readiness probes) configured?
   - Are security contexts and RBAC properly defined?
   - Are ConfigMaps and Secrets used appropriately?
   - Is the deployment strategy suitable (rolling update, etc.)?

3. **Jenkins/CI-CD Pipelines**:
   - Are pipeline stages logically organized?
   - Are error handling and notifications properly configured?
   - Are credentials and secrets managed securely?
   - Are build artifacts properly managed?
   - Is the pipeline efficient and follows best practices?

4. **Groovy Scripts**:
   - Is the code clean and maintainable?
   - Are error handling mechanisms in place?
   - Are Jenkins APIs used correctly?
   - Is the script following Groovy best practices?

5. **General DevOps Best Practices**:
   - Is the configuration maintainable and scalable?
   - Are there proper comments and documentation?
   - Are naming conventions followed?
   - Is the solution production-ready?
   - Are there any security vulnerabilities?

Provide a review with:
- Decision: APPROVED, NEEDS_IMPROVEMENT, or REJECTED
- Summary: Brief summary of your review
- Comments: List of specific positive comments (if approved)
- Issues: List of issues found (if needs improvement or rejected)
- Suggestions: List of suggestions for improvement (if needs improvement)

Format your response as:
Decision: [APPROVED/NEEDS_IMPROVEMENT/REJECTED]
Summary: [your summary]
Comments: [comment 1], [comment 2]
Issues: [issue 1], [issue 2]
Suggestions: [suggestion 1], [suggestion 2]
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
