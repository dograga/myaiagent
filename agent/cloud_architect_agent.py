"""
Cloud Architect Agent - Expert in Google Cloud Platform
Specializes in security, DevOps, resiliency, networks, and regulatory compliance
"""
from typing import Dict, Any, Optional, Union, List
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain_google_vertexai import VertexAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Custom VertexAI wrapper that ensures string output
class VertexAIWrapper(VertexAI):
    """Wrapper around VertexAI that ensures string output."""
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the VertexAI API and ensure string output."""
        try:
            result = super()._call(prompt, stop, run_manager, **kwargs)
        except Exception as e:
            if hasattr(e, 'args') and len(e.args) > 0:
                result = str(e.args[0])
            else:
                raise
        
        # Handle list responses
        if isinstance(result, list):
            if len(result) > 0:
                if isinstance(result[0], dict) and 'text' in result[0]:
                    result = ' '.join(str(item.get('text', item)) for item in result)
                else:
                    result = ' '.join(str(item) for item in result)
            else:
                result = ""
        
        # Handle dict responses
        if isinstance(result, dict):
            if 'text' in result:
                result = result['text']
            else:
                result = str(result)
        
        # Ensure string output
        if not isinstance(result, str):
            result = str(result)
        
        return result
    
    def predict(self, text: str, stop: Optional[List[str]] = None) -> str:
        """Override predict to ensure string output."""
        result = super().predict(text, stop)
        if isinstance(result, list):
            result = ' '.join(str(item) for item in result)
        return str(result)
    
    def generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs) -> Any:
        """Override generate to ensure string output in generations."""
        from langchain.schema import Generation, LLMResult
        
        try:
            result = super().generate(prompts, stop, **kwargs)
        except Exception as e:
            error_str = str(e)
            if 'validation error' in error_str.lower() and 'input_type=list' in error_str:
                return LLMResult(generations=[[Generation(text="Thought: I need to respond in plain text format.\nFinal Answer: I understand.")]])
            else:
                return LLMResult(generations=[[Generation(text=f"Error in generation: {str(e)}")]])
        
        # Process all generations to ensure text is a string
        try:
            for generation_list in result.generations:
                for generation in generation_list:
                    if hasattr(generation, 'text'):
                        text_value = generation.text
                        
                        # Handle list
                        if isinstance(text_value, list):
                            if len(text_value) > 0:
                                if isinstance(text_value[0], dict):
                                    extracted = []
                                    for item in text_value:
                                        if 'text' in item:
                                            extracted.append(str(item['text']))
                                        elif 'content' in item:
                                            extracted.append(str(item['content']))
                                        else:
                                            extracted.append(str(item))
                                    text_value = ' '.join(extracted) if extracted else str(text_value[0])
                                else:
                                    text_value = ' '.join(str(item) for item in text_value)
                            else:
                                text_value = ""
                        
                        # Handle dict
                        elif isinstance(text_value, dict):
                            if 'text' in text_value:
                                text_value = str(text_value['text'])
                            elif 'content' in text_value:
                                text_value = str(text_value['content'])
                            else:
                                text_value = str(text_value)
                        
                        # Ensure string
                        if not isinstance(text_value, str):
                            text_value = str(text_value)
                        
                        generation.text = text_value
        except Exception as e:
            return LLMResult(generations=[[Generation(text=f"Processing error: {str(e)}")]])
        
        return result



class CloudArchitectAgent:
    """Cloud Architect Agent specialized in Google Cloud Platform - Consulting only."""
    
    def __init__(self, project_root: str = ".", auto_approve: bool = True):
        self.project_root = project_root
        self.auto_approve = auto_approve
        
        gcp_project = os.getenv("GCP_PROJECT_ID")
        gcp_location = os.getenv("GCP_LOCATION", "us-central1")
        model_name = os.getenv("VERTEX_MODEL_NAME", "text-bison@002")
        
        if not gcp_project:
            raise RuntimeError(
                "GCP_PROJECT_ID is not set. Please configure it in your .env file."
            )
        
        try:
            self.llm = VertexAIWrapper(
                model_name=model_name,
                project=gcp_project,
                location=gcp_location,
                max_output_tokens=2048,
                temperature=0.2,  # Lower temperature for more measured responses
                top_p=0.95,
                top_k=40,
                verbose=True
            )
        except Exception as e:
            error_msg = str(e)
            suggestions = []
            
            if "404" in error_msg:
                suggestions.append(f"The model '{model_name}' might not be available in region '{gcp_location}'")
            elif "403" in error_msg:
                suggestions.append("Permission denied - check your GCP project permissions")
            
            suggestion_text = "\n  - ".join(suggestions)
            raise RuntimeError(
                f"Failed to initialize VertexAI: {error_msg}\n\nSuggestions:\n  - {suggestion_text}"
            )
            
        self.agent = self._create_agent()

    
    def _create_agent(self) -> LLMChain:
        """Create the Cloud Architect LLM chain."""
        
        template = """You are an expert Cloud Architect specializing in Google Cloud Platform (GCP).

**YOUR EXPERTISE:**
- **Security:** IAM, Security Command Center, VPC Service Controls, KMS, Secret Manager, Cloud Armor
- **DevOps:** Cloud Build, Cloud Deploy, Artifact Registry, GKE, Cloud Run, Infrastructure as Code (Terraform, Deployment Manager)
- **Resiliency:** High availability, disaster recovery, multi-region deployments, load balancing, autoscaling
- **Networks:** VPC design, Cloud Load Balancing, Cloud CDN, Cloud Interconnect, VPN, firewall rules, network security
- **Regulatory Compliance:** SOC 2, ISO 27001, HIPAA, PCI DSS, GDPR, compliance frameworks and controls

**YOUR APPROACH:**
- Provide well-measured, thoughtful responses based on GCP best practices
- Consider security implications in all recommendations
- Balance performance, cost, and security in architectural decisions
- Reference specific GCP services and features when appropriate
- Consider regulatory and compliance requirements
- Provide detailed explanations with reasoning

**YOUR ROLE:**
- You are a CONSULTING-ONLY agent - you provide guidance and recommendations
- You do NOT have access to file operations or tools
- You provide architectural advice, design patterns, and best practices
- Your responses should be comprehensive and actionable for implementation by others

**CRITICAL RESPONSE REQUIREMENTS:**
1. **NEVER** respond with just "I understand" or simple acknowledgments
2. **ALWAYS** analyze the requirements thoroughly
3. **ALWAYS** provide comprehensive responses with:
   - What you analyzed
   - Why you made specific architectural decisions
   - Security and compliance considerations
   - Best practices applied
   - Recommendations for improvement

**OUTPUT FORMAT:**
Provide your response directly in this structured format: 

**Summary:**
[Brief overview of the solution/analysis]

**Architectural Decisions:**
1. [Decision 1 with reasoning and GCP services used]
2. [Decision 2 with reasoning and GCP services used]
3. [Decision 3 with reasoning and GCP services used]

**Security Considerations:**
[Detailed security analysis including IAM, encryption, network security, etc.]

**Compliance & Regulatory Notes:**
[Relevant compliance considerations and controls]

**Resiliency & High Availability:**
[HA design, disaster recovery, failover strategies]

**Best Practices Applied:**
[GCP best practices and Well-Architected Framework principles]

**Recommendations:**
[Additional recommendations for optimization, cost, or security]

**CRITICAL RULES:**
- **NEVER** respond with just "I understand" - always provide detailed architectural guidance
- **ALWAYS** provide comprehensive responses with the format shown above
- **ALWAYS** consider security, compliance, and resiliency in your recommendations
- You are consulting-only - provide guidance that others can implement

Begin!

Previous conversation history:
{history}

Question: {input}"""
        
        # Create memory
        memory = ConversationBufferWindowMemory(
            memory_key="history",
            k=5,
            return_messages=True
        )
        
        # Create prompt template
        prompt = PromptTemplate(
            input_variables=["input", "history"],
            template=template
        )
        
        # Create the LLM chain (no tools needed for consulting)
        llm_chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            memory=memory,
            verbose=True
        )
        
        return llm_chain
    
    def run(self, query: str, return_details: bool = False) -> Union[str, Dict[str, Any]]:
        """Run the agent with the given query."""
        # Format the query with history
        result = self.agent.predict(input=query)
        
        if return_details:
            return {
                "output": result,
                "intermediate_steps": []  # No tools, so no intermediate steps
            }
        else:
            return result


