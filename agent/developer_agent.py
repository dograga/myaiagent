from typing import List, Dict, Any, Optional, Union
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.agents.agent import AgentOutputParser
from langchain.chains import LLMChain
from langchain.prompts import StringPromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import AgentAction, AgentFinish
from langchain_google_vertexai import VertexAI
from tools.file_operations import FileOperations
import json
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Custom prompt template for the agent
class CustomPromptTemplate(StringPromptTemplate):
    template: str
    tools: List[Tool]
    
    def format(self, **kwargs) -> str:
        # Get the intermediate steps
        intermediate_steps = kwargs.pop("intermediate_steps")
        
        # Format the tools and tool names
        tools = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        tool_names = ", ".join([tool.name for tool in self.tools])
        
        # Format the intermediate steps
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += f"Thought: {action.log}\n"
            thoughts += f"Observation: {observation}\n"
        
        # Set the agent_scratchpad variable to record what was previously done
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = tools
        kwargs["tool_names"] = tool_names
        
        return self.template.format(**kwargs)

class DeveloperAgent:
    def __init__(self, project_root: str = "."):
        # Initialize file operations
        self.file_ops = FileOperations(project_root)
        
        # Initialize VertexAI with Application Default Credentials (ADC)
        # Ensure you've run: gcloud auth application-default login
        gcp_project = os.getenv("GCP_PROJECT_ID")
        gcp_location = os.getenv("GCP_LOCATION", "us-central1")
        model_name = os.getenv("VERTEX_MODEL_NAME", "text-bison@002")
        
        if not gcp_project:
            raise RuntimeError(
                "GCP_PROJECT_ID is not set. Please configure it in your .env file."
            )
        
        try:
            # Create a wrapper to handle list responses
            from langchain.llms.base import BaseLLM
            
            base_llm = VertexAI(
                model_name=model_name,
                project=gcp_project,
                location=gcp_location,
                max_output_tokens=2048,  # Increased for complex projects
                temperature=0.2,
                top_p=0.8,
                top_k=40,
                verbose=True
            )
            
            # Wrap the LLM to ensure string output
            self.llm = self._create_llm_wrapper(base_llm)
        except Exception as e:
            error_msg = str(e)
            suggestions = []
            
            if "404" in error_msg:
                suggestions.append(f"The model '{model_name}' might not be available in region '{gcp_location}'")
                suggestions.append(f"Try enabling the API: gcloud services enable aiplatform.googleapis.com --project={gcp_project}")
                suggestions.append(f"List available models: gcloud ai models list --region={gcp_location}")
                suggestions.append("Try a different model by setting VERTEX_MODEL_NAME in .env (e.g., text-bison@002, gemini-pro)")
            elif "403" in error_msg:
                suggestions.append("Permission denied - check your GCP project permissions")
                suggestions.append(f"Enable Vertex AI API: gcloud services enable aiplatform.googleapis.com --project={gcp_project}")
            else:
                suggestions.append("Make sure you've authenticated with: gcloud auth application-default login")
            
            suggestion_text = "\n  - ".join(suggestions)
            raise RuntimeError(
                f"Failed to initialize VertexAI: {error_msg}\n\nSuggestions:\n  - {suggestion_text}"
            )
            
        
        # Define tools
        self.tools = self._setup_tools()
        
        # Set up the agent
        self.agent = self._create_agent()
    
    def _create_llm_wrapper(self, base_llm):
        """Create a wrapper that ensures string output from the LLM."""
        class LLMWrapper:
            def __init__(self, llm):
                self.llm = llm
            
            def __call__(self, prompt, stop=None):
                result = self.llm(prompt, stop=stop)
                # Handle list responses
                if isinstance(result, list):
                    result = ' '.join(str(item) for item in result)
                return str(result)
            
            def predict(self, text, stop=None):
                result = self.llm.predict(text, stop=stop)
                if isinstance(result, list):
                    result = ' '.join(str(item) for item in result)
                return str(result)
            
            def __getattr__(self, name):
                return getattr(self.llm, name)
        
        return LLMWrapper(base_llm)
    
    def _write_file_wrapper(self, input_str: str) -> Dict[str, str]:
        """Wrapper for write_file that parses JSON input."""
        try:
            data = json.loads(input_str)
            file_path = data.get('file_path')
            content = data.get('content')
            if not file_path or content is None:
                return {"status": "error", "message": "Both 'file_path' and 'content' are required"}
            return self.file_ops.write_file(file_path, content)
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON input. Expected format: {\"file_path\": \"path\", \"content\": \"text\"}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _append_to_file_wrapper(self, input_str: str) -> Dict[str, str]:
        """Wrapper for append_to_file that parses JSON input."""
        try:
            data = json.loads(input_str)
            file_path = data.get('file_path')
            content = data.get('content')
            if not file_path or content is None:
                return {"status": "error", "message": "Both 'file_path' and 'content' are required"}
            return self.file_ops.append_to_file(file_path, content)
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON input. Expected format: {\"file_path\": \"path\", \"content\": \"text\"}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _setup_tools(self) -> List[Tool]:
        """Set up the tools for the agent."""
        return [
            Tool(
                name="read_file",
                func=self.file_ops.read_file,
                description="Useful for reading the contents of a file. Input should be the file path relative to the project root."
            ),
            Tool(
                name="write_file",
                func=self._write_file_wrapper,
                description='Useful for writing content to a file. Input must be a JSON string with format: {"file_path": "path/to/file", "content": "text to write"}'
            ),
            Tool(
                name="append_to_file",
                func=self._append_to_file_wrapper,
                description='Useful for appending content to a file. Input must be a JSON string with format: {"file_path": "path/to/file", "content": "text to append"}'
            ),
            Tool(
                name="delete_file",
                func=self.file_ops.delete_file,
                description="Useful for deleting a file. Input should be the file path relative to the project root."
            ),
            Tool(
                name="list_directory",
                func=self.file_ops.list_directory,
                description="Useful for listing the contents of a directory. Input should be the directory path relative to the project root (default is '.')."
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create and return the agent executor."""
        # Define the prompt template
        template = """You are a helpful AI developer assistant that helps with code-related tasks like creating, reading, updating, and deleting files.
        
        You have access to the following tools:
        {tools}
        
        IMPORTANT: You MUST use the following format exactly:
        
        Question: the input question you must answer
        Thought: think about what to do next
        Action: the action to take, must be one of [{tool_names}]
        Action Input: the input to the action (use proper JSON format for write_file and append_to_file)
        Observation: the result of the action
        ... (repeat Thought/Action/Action Input/Observation as needed)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question
        
        CRITICAL: Always end with "Final Answer:" followed by your response. Never give a direct response without this format.
        
        Begin!
        
        Previous conversation history:
        {history}
        
        Question: {input}
        {agent_scratchpad}"""
        
        # Create the prompt
        prompt = CustomPromptTemplate(
            template=template,
            tools=self.tools,
            input_variables=["input", "intermediate_steps", "history"]
        )
        
        # Create the LLM chain
        llm_chain = LLMChain(llm=self.llm, prompt=prompt)
        
        # Define tool names
        tool_names = [tool.name for tool in self.tools]
        
        # Create the agent
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=CustomOutputParser(),
            stop=["\nObservation:"],
            allowed_tools=tool_names
        )
        
        # Create memory
        memory = ConversationBufferWindowMemory(
            memory_key="history",
            k=5,
            return_messages=True
        )
        
        # Create the agent executor
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            verbose=True,
            memory=memory
        )
    
    def run(self, query: str, return_details: bool = False) -> Union[str, Dict[str, Any]]:
        """Run the agent with the given query."""
        # Don't catch exceptions here - let them propagate to the API layer
        if return_details:
            # Capture intermediate steps for detailed response
            result = self.agent(query)
            return result
        else:
            result = self.agent.run(query)
            return result

# Custom output parser
class CustomOutputParser(AgentOutputParser):
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse the output of the LLM."""
        # Check if this is a final answer
        if "Final Answer:" in text:
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text
            )
        
        # Check if this contains Action and Action Input
        if "Action:" in text and "Action Input:" in text:
            try:
                # Extract the action part after the last "Action:" marker
                action_block = text.split("Action:")[-1]
                
                # Split by "Action Input:" to get action and input
                if "Action Input:" in action_block:
                    parts = action_block.split("Action Input:", 1)
                    action = parts[0].strip()
                    action_input = parts[1].strip()
                    
                    # Clean up the action input (remove quotes, newlines before observation)
                    if "\nObservation:" in action_input:
                        action_input = action_input.split("\nObservation:")[0].strip()
                    action_input = action_input.strip('"').strip("'").strip()
                    
                    return AgentAction(
                        tool=action,
                        tool_input=action_input,
                        log=text
                    )
            except Exception as e:
                # If parsing fails, treat as final answer
                pass
        
        # If we can't parse it as an action, treat it as a final answer
        # This handles cases where the LLM gives a direct response
        return AgentFinish(
            return_values={"output": text.strip()},
            log=text
        )
            
    def parse_ai_message(self, message: Dict[str, Any]) -> Union[AgentAction, AgentFinish]:
        """Parse the AI message."""
        return self.parse(message["content"])
