from typing import List, Dict, Any, Optional, Union, Mapping
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.agents.agent import AgentOutputParser
from langchain.chains import LLMChain
from langchain.prompts import StringPromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import AgentAction, AgentFinish
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain_google_vertexai import VertexAI
from tools.file_operations import FileOperations
import json
import os
import re
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
            # If there's an error, try to extract the result
            if hasattr(e, 'args') and len(e.args) > 0:
                result = str(e.args[0])
            else:
                raise
        
        # Handle list responses
        if isinstance(result, list):
            result = ' '.join(str(item) for item in result)
        
        # Ensure string output
        return str(result)
    
    def predict(self, text: str, stop: Optional[List[str]] = None) -> str:
        """Override predict to ensure string output."""
        result = super().predict(text, stop)
        if isinstance(result, list):
            result = ' '.join(str(item) for item in result)
        return str(result)

from langchain.prompts import BasePromptTemplate

class CustomPromptTemplate(BasePromptTemplate):
    def __init__(self, template: str, tools: List[Any], input_variables: List[str]):
        super().__init__(input_variables=input_variables)
        self.template = template
        self.tools = tools

    def format(self, **kwargs) -> str:
        # convert history list to readable text
        history = kwargs.get("history", "")
        if isinstance(history, list):
            history = "\n".join([
                h.content if hasattr(h, "content") else str(h)
                for h in history
            ])
            kwargs["history"] = history

        intermediate_steps = kwargs.pop("intermediate_steps", [])
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += f"\nThought: {action.log}\nObservation: {observation}\n"
        kwargs["agent_scratchpad"] = thoughts

        return self.template.format(**kwargs)
    
    def format_prompt(self, **kwargs) -> PromptValue:
        class SimplePromptValue(PromptValue):
            def __init__(self, text):
                self.text = text
            def to_string(self):
                return self.text
            def to_messages(self):
                return [{"role": "user", "content": self.text}]
        return SimplePromptValue(self.format(**kwargs))

class DeveloperAgent:
    def __init__(self, project_root: str = ".", auto_approve: bool = True):
        # Initialize file operations
        self.file_ops = FileOperations(project_root)
        self.auto_approve = auto_approve
        
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
            self.llm = VertexAIWrapper(
                model_name=model_name,
                project=gcp_project,
                location=gcp_location,
                max_output_tokens=2048,  # Increased for complex projects
                temperature=0.2,
                top_p=0.8,
                top_k=40,
                verbose=True
            )
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

    def _safe_parse_json(self, input_str: str) -> Optional[Dict[str, Any]]:
    #"""Attempt to safely parse a possibly malformed JSON string from the LLM."""
        try:
            return json.loads(input_str)
        except json.JSONDecodeError:
            # Try repairing common issues
            cleaned = input_str.strip()

            # Replace real newlines inside strings with escaped ones
            cleaned = cleaned.replace("\n", "\\n")

            # Sometimes model omits closing braces
            if not cleaned.endswith("}"):
                cleaned += "}"

            # Try again
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # Last resort: extract with regex
                match = re.search(r'"file_path"\s*:\s*"([^"]+)"', cleaned)
                content_match = re.search(r'"content"\s*:\s*"(.+)"', cleaned)
                if match and content_match:
                    return {"file_path": match.group(1), "content": content_match.group(1)}
        return None

    
    def _write_file_wrapper(self, input_str: str) -> Dict[str, str]:
        """Wrapper for write_file that parses JSON input."""
        try:
            # Try to parse as JSON first
            data = self._safe_parse_json(input_str)
            if not data:
                return {
                    "status": "error",
                    "message": f"Invalid JSON format. Could not parse input. "
                            f"Example: {{\"file_path\": \"example.py\", \"content\": \"def hello():\\\\n    print('Hi')\"}}"
                }

            file_path = data.get("file_path")
            content = data.get("content")

            if not file_path or content is None:
                return {"status": "error", "message": "Both 'file_path' and 'content' are required."}

            # Normalize escape sequences
            content = content.replace("\\n", "\n").replace("\\t", "\t")

            return self.file_ops.write_file(file_path, content)
        except json.JSONDecodeError as e:
            # Try to extract file_path and content manually as fallback
            try:
                # Look for file_path pattern - more flexible
                file_path_match = re.search(r'["\']file_path["\']\s*:\s*["\']([^"\'\\\\/]+)["\']', input_str)
                
                if file_path_match:
                    file_path = file_path_match.group(1)
                    
                    # Try multiple patterns for content
                    # Pattern 1: content with closing quote and brace
                    content_match = re.search(r'["\']content["\']\s*:\s*["\'](.+?)["\']\s*}', input_str, re.DOTALL)
                    
                    if not content_match:
                        # Pattern 2: content to end of string (unterminated)
                        content_match = re.search(r'["\']content["\']\s*:\s*["\'](.+)', input_str, re.DOTALL)
                    
                    if content_match:
                        content = content_match.group(1)
                        # Remove trailing quote and brace if present
                        content = content.rstrip('"}\' \n\r\t')
                        # Unescape common patterns
                        content = content.replace('\\n', '\n').replace('\\t', '\t')
                        content = content.replace('\\\\', '\\').replace("\\\"", '"').replace("\\'", "'")
                        return self.file_ops.write_file(file_path, content)
            except Exception as fallback_error:
                # Log fallback error for debugging
                print(f"Fallback parser error: {fallback_error}")
            
            # Provide detailed error with example
            return {
                "status": "error", 
                "message": f"Invalid JSON format. Error: {str(e)}. You MUST close the JSON string properly. CORRECT FORMAT: {{\"file_path\": \"example.py\", \"content\": \"def hello():\\\\n    print('Hello')\"}}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Error writing file: {str(e)}"}
    
    def _append_to_file_wrapper(self, input_str: str) -> Dict[str, str]:
        """Wrapper for append_to_file that parses JSON input."""
        try:
            data = self._safe_parse_json(input_str)
            if not data:
                return {
                    "status": "error",
                    "message": f"Invalid JSON format. Could not parse input. "
                            f"Example: {{\"file_path\": \"example.py\", \"content\": \"def hello():\\\\n    print('Hi')\"}}"
                }

            file_path = data.get("file_path")
            content = data.get("content")

            if not file_path or content is None:
                return {"status": "error", "message": "Both 'file_path' and 'content' are required."}

            # Normalize escape sequences
            content = content.replace("\\n", "\n").replace("\\t", "\t")

            return self.file_ops.write_file(file_path, content)
        except json.JSONDecodeError as e:
            # Try to extract file_path and content manually as fallback
            try:
                file_path_match = re.search(r'["\']file_path["\']\s*:\s*["\']([^"\'\\\\/]+)["\']', input_str)
                
                if file_path_match:
                    file_path = file_path_match.group(1)
                    
                    # Try multiple patterns for content
                    content_match = re.search(r'["\']content["\']\s*:\s*["\'](.+?)["\']\s*}', input_str, re.DOTALL)
                    
                    if not content_match:
                        content_match = re.search(r'["\']content["\']\s*:\s*["\'](.+)', input_str, re.DOTALL)
                    
                    if content_match:
                        content = content_match.group(1)
                        content = content.rstrip('"}\' \n\r\t')
                        content = content.replace('\\n', '\n').replace('\\t', '\t')
                        content = content.replace('\\\\', '\\').replace("\\\"", '"').replace("\\'", "'")
                        return self.file_ops.append_to_file(file_path, content)
            except Exception as fallback_error:
                print(f"Fallback parser error: {fallback_error}")
            
            return {
                "status": "error", 
                "message": f"Invalid JSON format. Error: {str(e)}. You MUST close the JSON string properly. CORRECT FORMAT: {{\"file_path\": \"example.py\", \"content\": \"def goodbye():\\\\n    print('Bye')\"}}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Error appending to file: {str(e)}"}
    
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
                description='REQUIRED for creating or updating files. You MUST use this tool to actually modify file contents. Just reading a file and thinking about changes does NOT modify it. Input MUST be valid JSON on ONE LINE: {"file_path": "path/to/file", "content": "text to write"}. Example: {"file_path": "test.py", "content": "def hello():\\n    print(\'Hello\')"}'
            ),
            Tool(
                name="append_to_file",
                func=self._append_to_file_wrapper,
                description='Useful for appending content to a file. Input MUST be valid JSON on ONE LINE: {"file_path": "path/to/file", "content": "text to append"}. Example: {"file_path": "test.py", "content": "\\ndef goodbye():\\n    print(\'Bye\')"}'
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
        # Define the prompt template based on approval mode
        if self.auto_approve:
            template = """You are a helpful AI developer assistant that helps with code-related tasks like creating, reading, updating, and deleting files.

IMPORTANT BEHAVIOR: You are in AUTO-EXECUTE mode. When asked to make changes:
1. IMMEDIATELY execute the changes using the appropriate tools
2. DO NOT just describe what you would do
3. DO NOT say "I have modified" or "I have updated" unless you actually used a tool
4. Take action first, then report what you did

You have access to the following tools:
{tools}

You MUST use the following format exactly:

Question: the input question you must answer
Thought: I need to use [tool_name] to make this change
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I have completed the requested actions
Final Answer: [Describe what you actually did and the results]

CRITICAL RULES - READ CAREFULLY:
- You CANNOT modify files by just thinking about it - you MUST use write_file or append_to_file tools
- NEVER say "I have modified the file" without an Action/Observation showing the tool was used
- If you read a file and identified changes needed, you MUST then use write_file to apply them
- After reading a file, the next step is ALWAYS an Action (write_file/append_to_file), not Final Answer
- The Observation will confirm if the file was actually modified
- Only report success in Final Answer if you see "File written successfully" in an Observation

JSON FORMAT FOR write_file AND append_to_file:
For write_file or append_to_file, the Action Input MUST be valid JSON on a single line.
Use \\n for newlines. Use SINGLE quotes inside Python strings to avoid escaping.

CORRECT EXAMPLES:
Action: write_file
Action Input: {{"file_path": "test.py", "content": "def hello():\\n    print('Hello, World!')\\n"}}

Action: write_file
Action Input: {{"file_path": "calc.py", "content": "def add(a, b):\\n    return a + b\\n"}}
Action: append_to_file
Action Input: {{"file_path": "test.py", "content": "\\ndef goodbye():\\n    print('Goodbye!')\\n"}}

KEY RULES:
- Use \\n for line breaks (NOT actual newlines)
- Use single quotes ' inside Python code (NOT double quotes ")
- Keep JSON on ONE line
- ALWAYS close the JSON string with "}}" at the end
- Example: print('hello') NOT print(\\"hello\")
- COMPLETE FORMAT: {{"file_path": "file.py", "content": "code here"}}

Begin!

Previous conversation history:
{history}
{{ ... }}

Action: append_to_file
Action Input: {{"file_path": "test.py", "content": "\\ndef goodbye():\\n    print('Goodbye!')\\n"}}

KEY RULES:
- Use \\n for line breaks (NOT actual newlines)
- Use single quotes ' inside Python code (NOT double quotes ")
- Keep JSON on ONE line
- ALWAYS close the JSON string with "}}" at the end
- Example: print('hello') NOT print(\\"hello\")
- COMPLETE FORMAT: {{"file_path": "file.py", "content": "code here"}}

Begin!

Previous conversation history:
{history}
{{ ... }}
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
            memory=memory,
            max_iterations=10,  # Allow multiple steps
            early_stopping_method="generate",  # Don't stop early
            handle_parsing_errors=True  # Handle parsing errors gracefully
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
        # Handle list responses from LLM
        if isinstance(text, list):
            text = ' '.join(str(item) for item in text)
        
        # Ensure text is a string
        text = str(text)
        
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
