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
        
        if not gcp_project:
            raise RuntimeError(
                "GCP_PROJECT_ID is not set. Please configure it in your .env file."
            )
        
        try:
            self.llm = VertexAI(
                model_name="text-bison@001",
                project=gcp_project,
                location=gcp_location,
                max_output_tokens=1024,
                temperature=0.2,
                top_p=0.8,
                top_k=40,
                verbose=True
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize VertexAI: {str(e)}\n"
                f"Make sure you've authenticated with: gcloud auth application-default login"
            )
            
        
        # Define tools
        self.tools = self._setup_tools()
        
        # Set up the agent
        self.agent = self._create_agent()
    
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
                func=self.file_ops.write_file,
                description="Useful for writing content to a file. Input should be a JSON string with 'file_path' and 'content' keys."
            ),
            Tool(
                name="append_to_file",
                func=self.file_ops.append_to_file,
                description="Useful for appending content to a file. Input should be a JSON string with 'file_path' and 'content' keys."
            ),
            Tool(
                name="delete_file",
                func=self.file_ops.delete_file,
                description="Useful for deleting a file. Input should be the file path relative to the project root."
            ),
            Tool(
                name="list_directory",
                func=self.file_ops.list_directory,
                description="Useful for listing the contents of a directory. Input should be the directory path relative to the project root."
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create and return the agent executor."""
        # Define the prompt template
        template = """You are a helpful AI developer assistant. You can help with various development tasks.
        
        You have access to the following tools:
        {tools}
        
        Use the following format:
        
        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question
        
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
    
    def run(self, query: str) -> str:
        """Run the agent with the given query."""
        # Don't catch exceptions here - let them propagate to the API layer
        result = self.agent.run(query)
        return result

# Custom output parser
class CustomOutputParser(AgentOutputParser):
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse the output of the LLM."""
        if "Final Answer:" in text:
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text
            )
        
        try:
            action, action_input = text.split("Action:")[-1].split("Action Input:")
            action = action.strip()
            action_input = action_input.strip()
            
            return AgentAction(
                tool=action,
                tool_input=action_input.strip('"').strip("'"),
                log=text
            )
        except Exception as e:
            return AgentFinish(
                return_values={"output": f"Error parsing LLM output: {str(e)}. Original output: {text}"},
                log=text
            )
            
    def parse_ai_message(self, message: Dict[str, Any]) -> Union[AgentAction, AgentFinish]:
        """Parse the AI message."""
        return self.parse(message["content"])
