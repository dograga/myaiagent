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
        
        try:
            for generation_list in result.generations:
                for generation in generation_list:
                    if hasattr(generation, 'text'):
                        text_value = generation.text
                        
                        if isinstance(text_value, list):
                            if len(text_value) > 0:
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
                                    text_value = ' '.join(str(item) for item in text_value)
                            else:
                                text_value = ""
                        
                        elif isinstance(text_value, dict):
                            if 'text' in text_value:
                                text_value = str(text_value['text'])
                            elif 'content' in text_value:
                                text_value = str(text_value['content'])
                            elif 'output' in text_value:
                                text_value = str(text_value['output'])
                            else:
                                text_value = str(text_value)
                        
                        if not isinstance(text_value, str):
                            text_value = str(text_value)
                        
                        generation.text = text_value
        except Exception as e:
            return LLMResult(generations=[[Generation(text=f"Processing error: {str(e)}")]])
        
        return result

# Custom prompt template for the agent
class CustomPromptTemplate(BasePromptTemplate):
    template: str = Field(..., description="The main text template.")
    tools: List[Any] = Field(default_factory=list, description="Tools available to the agent.")

    def __init__(self, *, template: str, tools: List[Any], input_variables: List[str]):
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
        return StringPromptValue(text=self.format(**kwargs))

class DevOpsAgent:
    def __init__(self, project_root: str = ".", auto_approve: bool = True):
        self.file_ops = FileOperations(project_root)
        self.auto_approve = auto_approve
        self.project_root = project_root
        
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
                temperature=0,
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
            
        self.tools = self._setup_tools()
        self.agent = self._create_agent()

    def _safe_parse_json(self, input_str: str) -> Optional[Dict[str, Any]]:
        """Attempt to safely parse a possibly malformed JSON string from the LLM."""
        try:
            return json.loads(input_str)
        except json.JSONDecodeError:
            cleaned = input_str.strip()
            if not cleaned.endswith("}"):
                cleaned += "}"
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return None

    def _read_file_wrapper(self, file_path: str) -> Dict[str, Any]:
        """Wrapper for read_file that accepts a simple file path string."""
        file_path = file_path.strip().strip('"').strip("'")
        return self.file_ops.read_file(file_path)
    
    def _write_file_wrapper(self, input_str: str) -> Dict[str, str]:
        """Wrapper for write_file that parses JSON input."""
        try:
            data = self._safe_parse_json(input_str)
            if not data:
                return {
                    "status": "error",
                    "message": f"Invalid JSON format. Could not parse input. "
                                f"Example: {{\"file_path\": \"terraform/main.tf\", \"content\": \"resource \\\"aws_instance\\\" \\\"example\\\" {{\\n  ami = \\\"ami-123\\\"\\n}}\"}}"
                }

            file_path = data.get("file_path")
            content = data.get("content")

            if not file_path or content is None:
                return {"status": "error", "message": "Both 'file_path' and 'content' are required."}

            return self.file_ops.write_file(file_path, content)
        except json.JSONDecodeError as e:
            # Fallback parsing for malformed JSON
            try:
                file_path_match = re.search(r'["\']file_path["\']\s*:\s*["\']([^"\'\\\\/]+)["\']', input_str)
                
                if file_path_match:
                    file_path = file_path_match.group(1)
                    content_match = re.search(r'["\']content["\']\s*:\s*["\'](.+?)["\']\s*}', input_str, re.DOTALL)
                    if not content_match:
                        content_match = re.search(r'["\']content["\']\s*:\s*["\'](.+)', input_str, re.DOTALL)
                    
                    if content_match:
                        content = content_match.group(1)
                        content = content.rstrip('"}\' \n\r\t')
                        content = content.replace('\\n', '\n').replace('\\t', '\t')
                        content = content.replace('\\\\', '\\').replace('\\"', '"').replace('\\\'', "'")
                        
                        return self.file_ops.write_file(file_path, content)
            except Exception:
                pass
            
            return {
                "status": "error", 
                "message": f"Invalid JSON format. Error: {str(e)}. CORRECT FORMAT: {{\"file_path\": \"terraform/main.tf\", \"content\": \"resource \\\"aws_instance\\\" \\\"example\\\" {{\\n  ami = \\\"ami-123\\\"\\n}}\"}}"
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
                                f"Example: {{\"file_path\": \"Jenkinsfile\", \"content\": \"\\n\\nstage('Deploy') {{\\n  steps {{\\n    sh 'kubectl apply -f k8s/'\\n  }}\\n}}\"}}"
                }

            file_path = data.get("file_path")
            content = data.get("content")

            if not file_path or content is None:
                return {"status": "error", "message": "Both 'file_path' and 'content' are required."}

            return self.file_ops.append_to_file(file_path, content)
        except json.JSONDecodeError as e:
            return {
                "status": "error", 
                "message": f"Invalid JSON format. Error: {str(e)}. CORRECT FORMAT: {{\"file_path\": \"Jenkinsfile\", \"content\": \"\\n\\nstage('Deploy') {{\\n  steps {{\\n    sh 'kubectl apply -f k8s/'\\n  }}\\n}}\"}}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Error appending to file: {str(e)}"}

    def _modify_code_block_wrapper(self, input_str: str) -> Dict[str, str]:
        """Wrapper for surgical find-and-replace operations."""
        try:
            data = json.loads(input_str) 
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON for modify_code_block. Error: {str(e)}. Input: {input_str}"}

        file_path = data.get("file_path")
        search_block = data.get("search_block")
        replace_block = data.get("replace_block")

        if not all([file_path, search_block is not None, replace_block is not None]):
            return {"status": "error", "message": "Missing file_path, search_block, or replace_block."}

        # Read the file
        read_result = self.file_ops.read_file(file_path)
        if read_result['status'] == 'error':
            return read_result

        original_content = read_result['content']
        
        # Perform the replace operation
        if search_block not in original_content:
            return {"status": "error", "message": f"Search block not found in {file_path}. The agent must use 'read_file' to get the exact existing code before using this tool."}
            
        new_content = original_content.replace(search_block, replace_block, 1)
        
        return self.file_ops.write_file(file_path, new_content)

    def _setup_tools(self) -> List[Tool]:
        """Set up the tools for the DevOps agent."""
        return [
            Tool(
                name="read_file",
                func=self._read_file_wrapper,
                description='Reads the contents of a file (Terraform, Kubernetes manifests, Jenkinsfile, Groovy scripts, etc.). Input must be a simple string (just the file path). Example: terraform/main.tf or k8s/deployment.yaml'
            ),
            Tool(
                name="write_file",
                func=self._write_file_wrapper,
                description='Creates a new DevOps configuration file. Use ONLY for NEW files. Input: {"file_path": "path/to/file", "content": "complete file content"}. Use \\n for newlines. Example: {"file_path": "terraform/main.tf", "content": "resource \\"aws_instance\\" \\"web\\" {\\n  ami = \\"ami-123\\"\\n  instance_type = \\"t2.micro\\"\\n}"}'
            ),
            Tool(
                name="modify_code_block",
                func=self._modify_code_block_wrapper,
                description='**CRITICAL for existing files:** Surgically modifies a specific block in an existing configuration file. Use this for changing existing resources/stages/configurations. Input: {"file_path": "path/to/file", "search_block": "existing config to find", "replace_block": "new config block"}. The content can be **multi-line** and **DOES NOT REQUIRE \\n ESCAPING**.'
            ),
            Tool(
                name="append_to_file",
                func=self._append_to_file_wrapper,
                description='Adds NEW content (new resources/stages/configurations) to the END of an existing file. Do NOT use for modifying existing code. Always start content with \\n\\n for proper spacing. Input: {"file_path": "path/to/file", "content": "\\n\\nresource \\"aws_s3_bucket\\" \\"new_bucket\\" {\\n  bucket = \\"my-bucket\\"\\n}\\n"}'
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
        
        template = """You are an expert DevOps Engineer AI assistant specializing in:
- **Terraform**: Infrastructure as Code for cloud resources (AWS, GCP, Azure)
- **Kubernetes**: Container orchestration, deployments, services, ingress
- **Jenkins**: CI/CD pipelines, Jenkinsfiles, build automation
- **Groovy**: Jenkins pipeline scripting and automation

⚠️ CRITICAL INSTRUCTIONS ⚠️

**Your Communication Style:**
1. **ALWAYS explain the requirement clearly** - Start by explaining what you understand from the user's request
2. **Describe your actions in detail** - Explain what you're doing and why
3. **NEVER respond with just "I understand"** - Always provide detailed explanations of the solution
4. **Explain the solution or action taken** - After completing a task, explain what was done, what files were created/modified, and what the configuration does

**Example Good Response:**
"Based on your request, I understand you need a Terraform configuration to create an AWS EC2 instance with specific security groups. I will:
1. Create a main.tf file with the EC2 instance resource
2. Configure security groups to allow HTTP and SSH traffic
3. Set up proper tags for resource management

Let me create this configuration...

[After creating files]

I have created the Terraform configuration with the following components:
- main.tf: Defines an EC2 instance with t2.micro instance type
- The security group allows inbound traffic on ports 22 (SSH) and 80 (HTTP)
- Tags are applied for easy identification
- The configuration uses variables for flexibility

You can now run 'terraform init' and 'terraform apply' to provision these resources."

**Code Modification Rules:**
1. **To CREATE a new file:** Use **write_file**. You must use **\\n** for newlines in the JSON `content`.
2. **To MODIFY existing code:** Use **modify_code_block**. You **DO NOT** use **\\n** for newlines in the `search_block` or `replace_block`.
3. **To ADD NEW code at the end:** Use **append_to_file**. You must use **\\n** for newlines in the JSON `content`.

**Example: Using modify_code_block**
Action: read_file
Action Input: terraform/main.tf
Observation: resource "aws_instance" "web" {
  ami = "ami-123"
  instance_type = "t2.micro"
}

Thought: I need to change the instance type to t2.small for better performance.
Action: modify_code_block
Action Input: {{"file_path": "terraform/main.tf", "search_block": "resource \\"aws_instance\\" \\"web\\" {
  ami = \\"ami-123\\"
  instance_type = \\"t2.micro\\"
}", "replace_block": "resource \\"aws_instance\\" \\"web\\" {
  ami = \\"ami-123\\"
  instance_type = \\"t2.small\\"
}"}}

You have access to the following tools:
{tools}

OUTPUT FORMAT - CRITICAL:
Your response MUST be plain text following this exact format. DO NOT output JSON objects or dictionaries.

CORRECT FORMAT:
Thought: [Explain what you understand and what you plan to do]
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: [Explain what you have accomplished]
Final Answer: [Detailed explanation of the solution, what was created/modified, and how to use it]

CRITICAL RULES:
- **Always** use `read_file` first to get the exact content before using `modify_code_block`
- **NEVER** use `write_file` to modify an existing file. Use `modify_code_block` or `append_to_file`
- **ALWAYS** explain your understanding of the requirement
- **NEVER** give a final answer as just "I understand" - explain the solution in detail

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
            max_iterations=20,
            max_execution_time=300,
            early_stopping_method="force",
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
    
    def run(self, query: str, return_details: bool = False) -> Union[str, Dict[str, Any]]:
        """Run the agent with the given query."""
        if return_details:
            result = self.agent(query)
            return result
        else:
            result = self.agent.run(query)
            return result

# Custom output parser
class CustomOutputParser(AgentOutputParser):
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse the output of the LLM."""
        if isinstance(text, list):
            text = ' '.join(str(item) for item in text)
        
        text = str(text)
        
        if "Final Answer:" in text:
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text
            )
        
        if "Action:" in text and "Action Input:" in text:
            try:
                action_block = text.split("Action:")[-1]
                
                if "Action Input:" in action_block:
                    parts = action_block.split("Action Input:", 1)
                    action = parts[0].strip()
                    action_input = parts[1].strip()
                    
                    if "\nObservation:" in action_input:
                        action_input = action_input.split("\nObservation:")[0].strip()
                    
                    return AgentAction(
                        tool=action,
                        tool_input=action_input,
                        log=text
                    )
            except Exception:
                pass
        
        return AgentFinish(
            return_values={"output": text.strip()},
            log=text
        )
