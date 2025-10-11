from typing import List, Dict, Any, Optional, Union, Mapping
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.agents.agent import AgentOutputParser
from langchain.chains import LLMChain
from langchain.prompts import StringPromptTemplate, BasePromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import AgentAction, AgentFinish
from langchain_core.prompt_values import StringPromptValue
from langchain_core.prompt_values import PromptValue
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain_google_vertexai import VertexAI
from tools.file_operations import FileOperations
from pydantic import Field
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
        
        # Handle list responses - convert to string immediately
        if isinstance(result, list):
            if len(result) > 0:
                # If list contains dicts or objects, extract text
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
        
        # Ensure string output - force conversion
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
            # Call parent generate
            result = super().generate(prompts, stop, **kwargs)
        except Exception as e:
            # If generation fails due to validation, try to extract from error
            error_str = str(e)
            if 'validation error' in error_str.lower() and 'input_type=list' in error_str:
                # The error contains the actual list that failed validation
                # Return a simple text response
                return LLMResult(generations=[[Generation(text="Thought: I need to respond in plain text format.\nFinal Answer: I understand.")]])
            else:
                # Other errors
                return LLMResult(generations=[[Generation(text=f"Error in generation: {str(e)}")]])
        
        # Process all generations to ensure text is a string
        try:
            for generation_list in result.generations:
                for generation in generation_list:
                    if hasattr(generation, 'text'):
                        text_value = generation.text
                        
                        # Handle list of any type
                        if isinstance(text_value, list):
                            if len(text_value) > 0:
                                # If list contains dicts
                                if isinstance(text_value[0], dict):
                                    extracted = []
                                    for item in text_value:
                                        if 'text' in item:
                                            extracted.append(str(item['text']))
                                        elif 'content' in item:
                                            extracted.append(str(item['content']))
                                        elif 'output' in item:
                                            extracted.append(str(item['output']))
                                        else:
                                            extracted.append(str(item))
                                    text_value = ' '.join(extracted) if extracted else str(text_value[0])
                                else:
                                    # List of strings or other
                                    text_value = ' '.join(str(item) for item in text_value)
                            else:
                                text_value = ""
                        
                        # Handle dict
                        elif isinstance(text_value, dict):
                            if 'text' in text_value:
                                text_value = str(text_value['text'])
                            elif 'content' in text_value:
                                text_value = str(text_value['content'])
                            elif 'output' in text_value:
                                text_value = str(text_value['output'])
                            else:
                                text_value = str(text_value)
                        
                        # Ensure string
                        if not isinstance(text_value, str):
                            text_value = str(text_value)
                        
                        generation.text = text_value
        except Exception as e:
            # If processing fails, return safe response
            return LLMResult(generations=[[Generation(text=f"Processing error: {str(e)}")]])
        
        return result

# Custom prompt template for the agent
class CustomPromptTemplate(BasePromptTemplate):
    template: str = Field(..., description="The main text template.")
    tools: List[Any] = Field(default_factory=list, description="Tools available to the agent.")

    def __init__(self, *, template: str, tools: List[Any], input_variables: List[str]):
        # Pass all fields directly to BasePromptTemplate (Pydantic model)
        super().__init__(template=template, tools=tools, input_variables=input_variables)

    def format(self, **kwargs) -> str:
        # Handle history
        history = kwargs.get("history", "")
        if isinstance(history, list):
            history = "\n".join([
                h.content if hasattr(h, "content") else str(h)
                for h in history
            ])
            kwargs["history"] = history

        # Handle intermediate steps
        intermediate_steps = kwargs.pop("intermediate_steps", [])
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += f"\nThought: {action.log}\nObservation: {observation}\n"
        kwargs["agent_scratchpad"] = thoughts

        # Format tools and tool names for the template
        tools_str = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        tool_names = ", ".join([tool.name for tool in self.tools])
        kwargs["tools"] = tools_str
        kwargs["tool_names"] = tool_names

        return self.template.format(**kwargs)
    
    def format_prompt(self, **kwargs) -> PromptValue:
        #from langchain.schema import StringPromptValue
        return StringPromptValue(text=self.format(**kwargs))

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
                temperature=0,  # Set to 0 for deterministic output
                top_p=0.95,
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
        """Attempt to safely parse a possibly malformed JSON string from the LLM."""
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

    def _fix_python_formatting(self, content: str) -> str:
        """Auto-fix single-line Python code by adding proper newlines."""
        # First, check if content has LITERAL \n strings (not actual newlines)
        # This happens when LLM outputs backslash-n as two characters instead of escape sequence
        if '\\n' in content and '\n' not in content:
            # Convert literal \n to actual newlines
            content = content.replace('\\n', '\n')
            # Also handle other escape sequences
            content = content.replace('\\t', '\t')
            return content
        
        # If content already has actual newlines, check if it's properly formatted
        if '\n' in content:
            # Count lines - if it has newlines, assume it's formatted
            return content
        
        # Detect single-line Python code and fix it
        # Pattern: def func(): statement or class Name: statement
        if 'def ' in content or 'class ' in content or 'import ' in content:
            # Add newline after colons followed by non-whitespace
            import re
            # Replace ': ' with ':\n    ' for function/class definitions
            fixed = re.sub(r':\s+(?=\S)', ':\n    ', content)
            # Ensure ends with newline
            if not fixed.endswith('\n'):
                fixed += '\n'
            return fixed
        
        return content
    
    def _read_file_wrapper(self, file_path: str) -> Dict[str, Any]:
        """Wrapper for read_file that accepts a simple file path string."""
        # Clean up the input - remove any quotes or whitespace
        file_path = file_path.strip().strip('"').strip("'")
        return self.file_ops.read_file(file_path)
    
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

            # Auto-fix single-line Python code
            if file_path.endswith('.py'):
                content = self._fix_python_formatting(content)

            # Content is already properly decoded by JSON parser
            # JSON parser converts \n to actual newlines automatically
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

            # Auto-fix single-line Python code
            if file_path.endswith('.py'):
                content = self._fix_python_formatting(content)

            # Content is already properly decoded by JSON parser
            # No additional processing needed
            return self.file_ops.append_to_file(file_path, content)
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
                func=self._read_file_wrapper,
                description='Reads the contents of a file. Input must be a simple string (just the file path). Example: test.py or src/main.py'
            ),
            Tool(
                name="write_file",
                func=self._write_file_wrapper,
                description='Creates a new file or REPLACES entire file content. Use for: (1) Creating new files, (2) Modifying existing code. When modifying, provide the COMPLETE file content with your changes. Input: {"file_path": "path/to/file", "content": "complete file content"}. Example: {"file_path": "test.py", "content": "def hello():\\n    print(\'Hello\')"}'
            ),
            Tool(
                name="append_to_file",
                func=self._append_to_file_wrapper,
                description='Adds content to the END of an existing file. Use ONLY for adding NEW functions/classes to Python files. Do NOT use for modifying existing code. Always start content with \\n\\n for proper spacing. Input: {"file_path": "path/to/file", "content": "new code to add"}. Example: {"file_path": "test.py", "content": "\\n\\ndef goodbye():\\n    print(\'Bye\')"}'
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

⚠️ CRITICAL - READ THIS FIRST ⚠️
When writing Python code in JSON, you MUST use \\n (backslash-n) for line breaks.

EXAMPLE - This is EXACTLY what you must type:
Action Input: {{"file_path": "test.py", "content": "def hello():\\n    print('Hi')\\n"}}
                                                                    ↑↑        ↑↑
                                                            These are: backslash + n

This creates a file with MULTIPLE LINES:
def hello():
    print('Hi')

WRONG EXAMPLES - DO NOT DO THIS:
❌ {{"content": "def hello(): print('Hi')"}}  ← Missing \\n (creates single line)
❌ {{"content": "def hello():\\\\n    print('Hi')"}}  ← Double backslash (wrong)
✅ {{"content": "def hello():\\n    print('Hi')\\n"}}  ← Correct (single backslash + n)

APPEND EXAMPLE - When adding a function to existing file:
Existing file has: def hello():\\n    print('Hello')\\n

To add goodbye function, use append_to_file with:
Action Input: {{"file_path": "test.py", "content": "\\n\\ndef goodbye():\\n    print('Bye')\\n"}}
                                                      ↑↑↑↑
                                            Start with TWO \\n for blank line

Result: File will have BOTH functions on SEPARATE LINES:
def hello():
    print('Hello')

def goodbye():
    print('Bye')

IMPORTANT BEHAVIOR: You are in AUTO-EXECUTE mode. When asked to make changes:
1. IMMEDIATELY execute the changes using the appropriate tools
2. DO NOT just describe what you would do
3. DO NOT say "I have modified" or "I have updated" unless you actually used a tool
4. Take action first, then report what you did

You have access to the following tools:
{tools}

OUTPUT FORMAT - CRITICAL:
Your response MUST be plain text following this exact format. DO NOT output JSON objects or dictionaries.

CORRECT FORMAT:
Question: the input question you must answer
Thought: I need to use [tool_name] to make this change
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I have completed the requested actions
Final Answer: [Describe what you actually did and the results]

WRONG - DO NOT DO THIS:
❌ {{"thought": "I need to...", "action": "write_file"}}  // DO NOT output as JSON/dict
✅ Thought: I need to...
   Action: write_file  // Output as plain text

CRITICAL RULES - READ CAREFULLY:
- You CANNOT modify files by just thinking about it - you MUST use write_file or append_to_file tools
- NEVER say "I have modified the file" without an Action/Observation showing the tool was used
- If you read a file and identified changes needed, you MUST then use write_file to apply them
- After reading a file, the next step is ALWAYS an Action (write_file/append_to_file), not Final Answer
- The Observation will confirm if the file was actually modified
- Only report success in Final Answer if you see "File written successfully" in an Observation

HOW TO WORK WITH PYTHON FILES - CRITICAL INSTRUCTIONS:

TOOL INPUT FORMATS - IMPORTANT:
- read_file: Simple string (just the file path)
  Example: Action Input: test.py
- write_file: JSON object with file_path and content
  Example: Action Input: {{"file_path": "test.py", "content": "def hello():\\n    print('Hi')\\n"}}
- append_to_file: JSON object with file_path and content
  Example: Action Input: {{"file_path": "test.py", "content": "\\n\\ndef goodbye():\\n    print('Bye')\\n"}}

STEP-BY-STEP WORKFLOW:
1. Read the file first: Action: read_file, Action Input: test.py (just the filename, NO JSON)
2. Decide: Am I MODIFYING existing code OR ADDING new code?
3. Execute the appropriate action with JSON format

RULE 1 - MODIFYING EXISTING CODE (changing a function, adding docstring to existing function):
- Use: write_file
- Content: COMPLETE file with ALL functions (existing + modified)
- Format: Each line separated by \\n

RULE 2 - ADDING NEW CODE (new function, new class):
- Use: append_to_file  
- Content: ONLY the new code to add
- Format: Start with \\n\\n then the new code

FORMATTING PYTHON CODE - CRITICAL:

The JSON Action Input must be on ONE line. Use \\n to create line breaks in the Python code.

VISUAL EXAMPLE - How \\n works:
JSON Input (one line):
"def hello():\\n    print('Hi')\\n"

Becomes in the file (multiple lines):
def hello():
    print('Hi')

STEP-BY-STEP EXAMPLE:
If you want to create this Python code:
def greet(name):
    '''Greet a person'''
    return f'Hello, {{name}}!'

You write it in JSON as:
"def greet(name):\\n    '''Greet a person'''\\n    return f'Hello, {{name}}!'\\n"

Notice:
- After "def greet(name):" → add \\n
- After "'''Greet a person'''" → add \\n  
- After "return f'Hello, {{name}}!'" → add \\n
- Use 4 spaces for indentation: \\n    (\\n followed by 4 spaces)

CORRECT EXAMPLE 1 - Create file:
Action: write_file
Action Input: {{"file_path": "test.py", "content": "def hello():\\n    '''Say hello'''\\n    print('Hello')\\n"}}

Result in file:
def hello():
    '''Say hello'''
    print('Hello')

CORRECT EXAMPLE 2 - Add function:
Action: append_to_file
Action Input: {{"file_path": "test.py", "content": "\\n\\ndef goodbye():\\n    '''Say goodbye'''\\n    print('Bye')\\n"}}

Result added to file:

def goodbye():
    '''Say goodbye'''
    print('Bye')

CRITICAL RULES:
- Every line of Python code must end with \\n
- Indentation: use \\n followed by spaces (\\n    for 4 spaces)
- Use single quotes ' not double quotes "
- Use ''' for docstrings not \\\"\\\"\\\""

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
            memory=memory,
            max_iterations=10,  # Allow multiple steps
            early_stopping_method="force",  # Use 'force' instead of 'generate'
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
