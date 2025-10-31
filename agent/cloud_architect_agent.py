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
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image

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
                max_output_tokens=8192,
                temperature=0.3,
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

YOUR EXPERTISE:
- Security: IAM, Security Command Center, VPC Service Controls, KMS, Secret Manager, Cloud Armor
- DevOps: Cloud Build, Cloud Deploy, Artifact Registry, GKE, Cloud Run, Infrastructure as Code (Terraform, Deployment Manager)
- Resiliency: High availability, disaster recovery, multi-region deployments, load balancing, autoscaling
- Networks: VPC design, Cloud Load Balancing, Cloud CDN, Cloud Interconnect, VPN, firewall rules, network security
- Regulatory Compliance: SOC 2, ISO 27001, HIPAA, PCI DSS, GDPR, compliance frameworks and controls

YOUR ROLE:
You are a CONSULTING-ONLY agent providing architectural guidance and technical documentation. You do NOT have access to file operations or tools. Your responses should be professional, focused, and directly address the user's specific question.

RESPONSE GUIDELINES:

1. ANSWER THE SPECIFIC QUESTION ASKED
   - Focus on what the user actually needs
   - Don't provide comprehensive documentation unless explicitly requested
   - If asked about one topic (e.g., networking), focus on that topic only
   - Only cover security, compliance, monitoring, etc. if relevant to the question

2. SCOPE YOUR RESPONSE APPROPRIATELY
   - Simple questions deserve simple answers
   - Complex architecture requests deserve detailed documentation
   - Let the user's question guide the depth and breadth of your response

3. WHEN TO PROVIDE COMPREHENSIVE DOCUMENTATION
   Only provide full architecture documentation when the user:
   - Explicitly asks for a "design document" or "architecture document"
   - Requests a "complete solution" or "full architecture"
   - Asks for a "production-ready" or "enterprise" solution
   - Specifically mentions multiple aspects (security, networking, compliance, etc.)

4. DOCUMENTATION STYLE (when detailed responses are needed)
   - Use proper markdown headings (# ## ###) not bold text
   - Minimize use of bold/italic formatting - use sparingly for critical terms
   - Use bullet points with - or numbered lists with 1. 2. 3.
   - Include code examples or configuration snippets when helpful
   - Focus on WHAT to implement and HOW to configure it

5. FOR SIMPLE QUERIES
   - Provide direct, concise answers
   - Use simple formatting (paragraphs and bullet points)
   - Include relevant GCP services and best practices
   - Offer to elaborate if the user needs more detail

EXAMPLE RESPONSES:

Simple Question: "How do I set up Cloud Storage?"
Good Response: Brief explanation of Cloud Storage setup with key commands/steps

Bad Response: Full architecture document with security, networking, compliance, monitoring, etc.

Complex Question: "Design a production-ready e-commerce platform architecture"
Good Response: Comprehensive architecture document with all relevant sections

Previous conversation history:
{history}

Question: {input}

Response:"""
        
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
    
    def run(self, query: str, return_details: bool = False, image_paths: List[str] = None) -> Union[str, Dict[str, Any]]:
        """Run the agent with the given query and optional images."""
        
        # If images are provided, use native Vertex AI multimodal API
        if image_paths and len(image_paths) > 0:
            result = self._run_with_images(query, image_paths)
        else:
            # Use LangChain for text-only queries
            result = self.agent.predict(input=query)
        
        if return_details:
            return {
                "output": result,
                "intermediate_steps": []  # No tools, so no intermediate steps
            }
        else:
            return result
    
    def _run_with_images(self, query: str, image_paths: List[str]) -> str:
        """Run the agent with images using native Vertex AI API."""
        try:
            # Initialize Vertex AI
            gcp_project = os.getenv("GCP_PROJECT_ID")
            gcp_location = os.getenv("GCP_LOCATION", "us-central1")
            model_name = os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash-exp")
            
            # Check if model supports vision
            vision_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-2.5-pro", "gemini-2.5-flash"]
            if not any(vm in model_name for vm in vision_models):
                return f"Note: The current model ({model_name}) may not support image analysis. Please use a Gemini vision model.\n\nText query: {query}"
            
            vertexai.init(project=gcp_project, location=gcp_location)
            model = GenerativeModel(model_name)
            
            # Prepare content with images and text
            contents = []
            
            # Add images first
            for image_path in image_paths:
                try:
                    image = Image.load_from_file(image_path)
                    contents.append(Part.from_image(image))
                except Exception as e:
                    print(f"Error loading image {image_path}: {e}")
            
            # Add the query with the Cloud Architect prompt context
            prompt_context = """You are an expert Cloud Architect specializing in Google Cloud Platform (GCP).

Analyze the provided image(s) and respond to the user's specific question.

YOUR EXPERTISE:
- Security: IAM, Security Command Center, VPC Service Controls, KMS, Secret Manager, Cloud Armor
- DevOps: Cloud Build, Cloud Deploy, Artifact Registry, GKE, Cloud Run, Infrastructure as Code
- Resiliency: High availability, disaster recovery, multi-region deployments
- Networks: VPC design, Cloud Load Balancing, Cloud CDN, Cloud Interconnect, VPN
- Regulatory Compliance: SOC 2, ISO 27001, HIPAA, PCI DSS, GDPR

RESPONSE GUIDELINES:
- Focus on what the user actually asks about the image(s)
- Don't provide comprehensive documentation unless explicitly requested
- Answer the specific question - if they ask about networking, focus on networking
- Only cover security, compliance, monitoring, etc. if relevant to the question
- Simple questions deserve simple answers
- Use proper markdown headings (# ## ###) when structure is needed
- Include specific GCP services and configurations relevant to the query

"""
            full_query = prompt_context + "\n\nUser Query: " + query
            contents.append(Part.from_text(full_query))
            
            # Generate response
            response = model.generate_content(
                contents,
                generation_config={
                    "max_output_tokens": 8192,
                    "temperature": 0.3,
                    "top_p": 0.95,
                    "top_k": 40,
                }
            )
            
            return response.text
            
        except Exception as e:
            error_msg = f"Error processing images: {str(e)}"
            print(error_msg)
            # Fallback to text-only processing
            return f"{error_msg}\n\nProcessing query without images:\n\n{self.agent.predict(input=query)}"


