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
from tools.jira_operations import JiraOperations
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
                                    text_value = ' '.join(extracted)
                                else:
                                    text_value = ' '.join(str(item) for item in text_value)
                            else:
                                text_value = ""
                        
                        if isinstance(text_value, dict):
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

class ProjectManagerAgent:
    def __init__(self, auto_approve: bool = True):
        self.jira_ops = JiraOperations()
        self.auto_approve = auto_approve
        self.project_root = os.getcwd()  # PM agent doesn't need project root but keeping for consistency
        
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

    def _get_epics_assigned_to_me_wrapper(self, input_str: str) -> str:
        """Wrapper for getting epics assigned to current user."""
        try:
            result = self.jira_ops.get_epics_assigned_to_user()
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _get_epic_details_wrapper(self, epic_key: str) -> str:
        """Wrapper for getting epic details."""
        try:
            epic_key = epic_key.strip().strip('"').strip("'")
            result = self.jira_ops.get_epic_details(epic_key)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _get_stories_in_epic_wrapper(self, epic_key: str) -> str:
        """Wrapper for getting stories in an epic."""
        try:
            epic_key = epic_key.strip().strip('"').strip("'")
            result = self.jira_ops.get_stories_in_epic(epic_key)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _get_story_details_wrapper(self, story_key: str) -> str:
        """Wrapper for getting story details."""
        try:
            story_key = story_key.strip().strip('"').strip("'")
            result = self.jira_ops.get_story_details(story_key)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _update_story_status_wrapper(self, input_str: str) -> str:
        """Wrapper for updating story status."""
        try:
            data = self._safe_parse_json(input_str)
            if not data:
                return json.dumps({"error": "Invalid JSON input"})
            
            story_key = data.get("story_key", "").strip()
            status = data.get("status", "").strip()
            
            if not story_key or not status:
                return json.dumps({"error": "Both story_key and status are required"})
            
            result = self.jira_ops.update_story_status(story_key, status)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _update_story_assignee_wrapper(self, input_str: str) -> str:
        """Wrapper for updating story assignee."""
        try:
            data = self._safe_parse_json(input_str)
            if not data:
                return json.dumps({"error": "Invalid JSON input"})
            
            story_key = data.get("story_key", "").strip()
            assignee = data.get("assignee", "").strip()
            
            if not story_key or not assignee:
                return json.dumps({"error": "Both story_key and assignee are required"})
            
            result = self.jira_ops.update_story_assignee(story_key, assignee)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _add_comment_to_story_wrapper(self, input_str: str) -> str:
        """Wrapper for adding comment to story."""
        try:
            data = self._safe_parse_json(input_str)
            if not data:
                return json.dumps({"error": "Invalid JSON input"})
            
            story_key = data.get("story_key", "").strip()
            comment = data.get("comment", "").strip()
            
            if not story_key or not comment:
                return json.dumps({"error": "Both story_key and comment are required"})
            
            result = self.jira_ops.add_comment_to_story(story_key, comment)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _search_issues_wrapper(self, jql: str) -> str:
        """Wrapper for searching issues with JQL."""
        try:
            jql = jql.strip().strip('"').strip("'")
            result = self.jira_ops.search_issues(jql)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _setup_tools(self) -> List[Tool]:
        """Set up the tools available to the agent."""
        return [
            Tool(
                name="get_my_epics",
                func=self._get_epics_assigned_to_me_wrapper,
                description="Get all epics assigned to me. Input: empty string or 'me'. Returns list of epics with their keys, summaries, and statuses."
            ),
            Tool(
                name="get_epic_details",
                func=self._get_epic_details_wrapper,
                description="Get detailed information about a specific epic. Input: epic key (e.g., 'PROJ-123'). Returns epic details including summary, status, assignee, description."
            ),
            Tool(
                name="get_stories_in_epic",
                func=self._get_stories_in_epic_wrapper,
                description="Get all stories in a specific epic. Input: epic key (e.g., 'PROJ-123'). Returns list of stories with their keys, summaries, statuses, and assignees."
            ),
            Tool(
                name="get_story_details",
                func=self._get_story_details_wrapper,
                description="Get detailed information about a specific story. Input: story key (e.g., 'PROJ-456'). Returns story details including summary, status, assignee, description, priority."
            ),
            Tool(
                name="update_story_status",
                func=self._update_story_status_wrapper,
                description='Update the status of a story. Input: JSON with story_key and status. Example: {"story_key": "PROJ-456", "status": "In Progress"}. Returns success or error message.'
            ),
            Tool(
                name="update_story_assignee",
                func=self._update_story_assignee_wrapper,
                description='Update the assignee of a story. Input: JSON with story_key and assignee username. Example: {"story_key": "PROJ-456", "assignee": "john.doe"}. Returns success or error message.'
            ),
            Tool(
                name="add_comment_to_story",
                func=self._add_comment_to_story_wrapper,
                description='Add a comment to a story. Input: JSON with story_key and comment text. Example: {"story_key": "PROJ-456", "comment": "Updated the implementation"}. Returns success or error message.'
            ),
            Tool(
                name="search_jira_issues",
                func=self._search_issues_wrapper,
                description='Search for Jira issues using JQL (Jira Query Language). Input: JQL query string. Example: "project = PROJ AND status = \\"In Progress\\"". Returns list of matching issues.'
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create and return the agent executor."""
        
        template = """You are an expert Project Manager AI assistant specializing in Jira project management.

**Your Expertise:**
- Reading and analyzing Jira epics and stories
- Providing status updates and summaries
- Updating story statuses and assignments
- Tracking project progress
- Answering questions about epics and stories

⚠️ CRITICAL INSTRUCTIONS ⚠️

**Your Communication Style:**
1. **ALWAYS explain what you found** - Provide clear summaries of the data
2. **Present information in organized format** - Use bullet points and clear structure
3. **NEVER respond with just "I understand"** - Always provide the actual information requested
4. **Be proactive** - Suggest relevant follow-up actions when appropriate

**Example Good Response:**
"I've retrieved your assigned epics from Jira. Here's what I found:

**Your Assigned Epics (3 total):**

1. **PROJ-123: User Authentication System**
   - Status: In Progress
   - Created: 2024-01-15
   - Stories: 8 total (5 done, 2 in progress, 1 to do)

2. **PROJ-145: Payment Integration**
   - Status: To Do
   - Created: 2024-01-20
   - Stories: 5 total (all to do)

3. **PROJ-167: Mobile App Redesign**
   - Status: In Progress
   - Created: 2024-01-10
   - Stories: 12 total (8 done, 3 in progress, 1 blocked)

Would you like me to provide details on any specific epic or its stories?"

**Tool Usage Rules:**
1. **To get your epics:** Use **get_my_epics**
2. **To get stories in an epic:** Use **get_stories_in_epic** with the epic key
3. **To update a story:** Use **update_story_status** or **update_story_assignee** with proper JSON
4. **To search:** Use **search_jira_issues** with JQL query

You have access to the following tools:
{tools}

OUTPUT FORMAT - CRITICAL:
Your response MUST be plain text following this exact format. DO NOT output raw JSON data directly.

⚠️ NEVER OUTPUT RAW JSON DIRECTLY ⚠️
DO NOT output raw Jira data in your response.
ALWAYS format the data in a human-readable way.

CORRECT FORMAT:
Thought: [Explain what you need to do to answer the question]
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: [Explain what you found and how you'll present it]
Final Answer: [Well-formatted, human-readable summary of the information]

WRONG - DO NOT DO THIS:
{{"status": "success", "epics": [{{"key": "PROJ-123"}}]}}

RIGHT - DO THIS:
Thought: I need to get the user's assigned epics
Action: get_my_epics
Action Input: me
Observation: {{"status": "success", "total": 2, "epics": [...]}}
Thought: I found 2 epics assigned to the user. Let me format this nicely.
Final Answer: You have 2 epics assigned to you: 1. PROJ-123: User Authentication (In Progress), 2. PROJ-145: Payment Integration (To Do)

CRITICAL RULES:
- **Always** start with "Thought:" - never output raw JSON directly
- **Always** format Jira data in human-readable format
- **Present data clearly** with proper structure and formatting
- **NEVER** give a final answer as just "I understand" - provide the actual information

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
            max_iterations=10,
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
