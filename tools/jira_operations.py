"""
Jira Operations Tool
Provides read and update operations for Jira epics and stories.
"""

import os
import requests
from typing import Dict, List, Any, Optional
from requests.auth import HTTPBasicAuth
import json


class JiraOperations:
    """Handle Jira API operations for epics and stories."""
    
    def __init__(self, jira_url: Optional[str] = None, username: Optional[str] = None, api_token: Optional[str] = None):
        """
        Initialize Jira operations.
        
        Args:
            jira_url: Jira instance URL (e.g., https://your-domain.atlassian.net)
            username: Jira username/email
            api_token: Jira API token or password
        """
        self.jira_url = jira_url or os.getenv("JIRA_URL", "")
        self.username = username or os.getenv("JIRA_USERNAME", "")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN", "")
        
        if not self.jira_url:
            raise ValueError("JIRA_URL must be provided via environment variable or parameter")
        if not self.username:
            raise ValueError("JIRA_USERNAME must be provided via environment variable or parameter")
        if not self.api_token:
            raise ValueError("JIRA_API_TOKEN must be provided via environment variable or parameter")
        
        # Remove trailing slash from URL
        self.jira_url = self.jira_url.rstrip('/')
        self.auth = HTTPBasicAuth(self.username, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a request to Jira API.
        
        Args:
            method: HTTP method (GET, POST, PUT)
            endpoint: API endpoint
            data: Request payload
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.jira_url}/rest/api/3/{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, auth=self.auth)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, auth=self.auth, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, auth=self.auth, json=data)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            
            # Some endpoints return empty responses
            if response.status_code == 204 or not response.content:
                return {"status": "success", "message": "Operation completed successfully"}
            
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error {e.response.status_code}: {e.response.text}"
            return {"error": error_msg}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON response"}
    
    def get_epics_assigned_to_user(self, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all epics assigned to a specific user.
        
        Args:
            username: Jira username (defaults to authenticated user)
            
        Returns:
            Dictionary with status and list of epics
        """
        user = username or self.username
        
        # JQL query to find epics assigned to user
        jql = f'issuetype = Epic AND assignee = "{user}" ORDER BY created DESC'
        
        params = {
            "jql": jql,
            "maxResults": 100,
            "fields": ["summary", "status", "assignee", "created", "updated", "description", "key"]
        }
        
        endpoint = f"search?jql={requests.utils.quote(jql)}&maxResults=100&fields=summary,status,assignee,created,updated,description,key"
        result = self._make_request("GET", endpoint)
        
        if "error" in result:
            return result
        
        epics = []
        for issue in result.get("issues", []):
            epics.append({
                "key": issue["key"],
                "summary": issue["fields"].get("summary", ""),
                "status": issue["fields"].get("status", {}).get("name", "Unknown"),
                "assignee": issue["fields"].get("assignee", {}).get("displayName", "Unassigned") if issue["fields"].get("assignee") else "Unassigned",
                "created": issue["fields"].get("created", ""),
                "updated": issue["fields"].get("updated", ""),
                "description": issue["fields"].get("description", "")
            })
        
        return {
            "status": "success",
            "total": len(epics),
            "epics": epics
        }
    
    def get_epic_details(self, epic_key: str) -> Dict[str, Any]:
        """
        Get details of a specific epic.
        
        Args:
            epic_key: Epic key (e.g., PROJ-123)
            
        Returns:
            Dictionary with epic details
        """
        endpoint = f"issue/{epic_key}"
        result = self._make_request("GET", endpoint)
        
        if "error" in result:
            return result
        
        fields = result.get("fields", {})
        return {
            "status": "success",
            "epic": {
                "key": result.get("key"),
                "summary": fields.get("summary", ""),
                "status": fields.get("status", {}).get("name", "Unknown"),
                "assignee": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned",
                "created": fields.get("created", ""),
                "updated": fields.get("updated", ""),
                "description": fields.get("description", ""),
                "priority": fields.get("priority", {}).get("name", "None") if fields.get("priority") else "None"
            }
        }
    
    def get_stories_in_epic(self, epic_key: str) -> Dict[str, Any]:
        """
        Get all stories in a specific epic.
        
        Args:
            epic_key: Epic key (e.g., PROJ-123)
            
        Returns:
            Dictionary with status and list of stories
        """
        # JQL query to find stories in epic
        jql = f'"Epic Link" = {epic_key} OR parent = {epic_key} ORDER BY created DESC'
        
        endpoint = f"search?jql={requests.utils.quote(jql)}&maxResults=100&fields=summary,status,assignee,created,updated,description,key,issuetype,priority"
        result = self._make_request("GET", endpoint)
        
        if "error" in result:
            return result
        
        stories = []
        for issue in result.get("issues", []):
            stories.append({
                "key": issue["key"],
                "type": issue["fields"].get("issuetype", {}).get("name", "Unknown"),
                "summary": issue["fields"].get("summary", ""),
                "status": issue["fields"].get("status", {}).get("name", "Unknown"),
                "assignee": issue["fields"].get("assignee", {}).get("displayName", "Unassigned") if issue["fields"].get("assignee") else "Unassigned",
                "priority": issue["fields"].get("priority", {}).get("name", "None") if issue["fields"].get("priority") else "None",
                "created": issue["fields"].get("created", ""),
                "updated": issue["fields"].get("updated", "")
            })
        
        return {
            "status": "success",
            "epic_key": epic_key,
            "total": len(stories),
            "stories": stories
        }
    
    def get_story_details(self, story_key: str) -> Dict[str, Any]:
        """
        Get details of a specific story.
        
        Args:
            story_key: Story key (e.g., PROJ-456)
            
        Returns:
            Dictionary with story details
        """
        endpoint = f"issue/{story_key}"
        result = self._make_request("GET", endpoint)
        
        if "error" in result:
            return result
        
        fields = result.get("fields", {})
        return {
            "status": "success",
            "story": {
                "key": result.get("key"),
                "type": fields.get("issuetype", {}).get("name", "Unknown"),
                "summary": fields.get("summary", ""),
                "status": fields.get("status", {}).get("name", "Unknown"),
                "assignee": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned",
                "reporter": fields.get("reporter", {}).get("displayName", "Unknown") if fields.get("reporter") else "Unknown",
                "priority": fields.get("priority", {}).get("name", "None") if fields.get("priority") else "None",
                "created": fields.get("created", ""),
                "updated": fields.get("updated", ""),
                "description": fields.get("description", "")
            }
        }
    
    def update_story_status(self, story_key: str, status: str) -> Dict[str, Any]:
        """
        Update the status of a story.
        
        Args:
            story_key: Story key (e.g., PROJ-456)
            status: New status (e.g., "In Progress", "Done")
            
        Returns:
            Dictionary with operation result
        """
        # First, get available transitions for the issue
        endpoint = f"issue/{story_key}/transitions"
        transitions_result = self._make_request("GET", endpoint)
        
        if "error" in transitions_result:
            return transitions_result
        
        # Find the transition ID for the desired status
        transition_id = None
        available_transitions = []
        
        for transition in transitions_result.get("transitions", []):
            transition_name = transition.get("to", {}).get("name", "")
            available_transitions.append(transition_name)
            if transition_name.lower() == status.lower():
                transition_id = transition.get("id")
                break
        
        if not transition_id:
            return {
                "error": f"Status '{status}' not found. Available transitions: {', '.join(available_transitions)}"
            }
        
        # Perform the transition
        data = {
            "transition": {
                "id": transition_id
            }
        }
        
        result = self._make_request("POST", f"issue/{story_key}/transitions", data)
        
        if "error" in result:
            return result
        
        return {
            "status": "success",
            "message": f"Story {story_key} status updated to '{status}'"
        }
    
    def update_story_assignee(self, story_key: str, assignee_username: str) -> Dict[str, Any]:
        """
        Update the assignee of a story.
        
        Args:
            story_key: Story key (e.g., PROJ-456)
            assignee_username: Username of the new assignee
            
        Returns:
            Dictionary with operation result
        """
        data = {
            "fields": {
                "assignee": {
                    "name": assignee_username
                }
            }
        }
        
        endpoint = f"issue/{story_key}"
        result = self._make_request("PUT", endpoint, data)
        
        if "error" in result:
            return result
        
        return {
            "status": "success",
            "message": f"Story {story_key} assignee updated to '{assignee_username}'"
        }
    
    def update_story_description(self, story_key: str, description: str) -> Dict[str, Any]:
        """
        Update the description of a story.
        
        Args:
            story_key: Story key (e.g., PROJ-456)
            description: New description text
            
        Returns:
            Dictionary with operation result
        """
        data = {
            "fields": {
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        endpoint = f"issue/{story_key}"
        result = self._make_request("PUT", endpoint, data)
        
        if "error" in result:
            return result
        
        return {
            "status": "success",
            "message": f"Story {story_key} description updated"
        }
    
    def add_comment_to_story(self, story_key: str, comment: str) -> Dict[str, Any]:
        """
        Add a comment to a story.
        
        Args:
            story_key: Story key (e.g., PROJ-456)
            comment: Comment text
            
        Returns:
            Dictionary with operation result
        """
        data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment
                            }
                        ]
                    }
                ]
            }
        }
        
        endpoint = f"issue/{story_key}/comment"
        result = self._make_request("POST", endpoint, data)
        
        if "error" in result:
            return result
        
        return {
            "status": "success",
            "message": f"Comment added to story {story_key}"
        }
    
    def search_issues(self, jql: str, max_results: int = 50) -> Dict[str, Any]:
        """
        Search for issues using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        endpoint = f"search?jql={requests.utils.quote(jql)}&maxResults={max_results}&fields=summary,status,assignee,created,updated,key,issuetype,priority"
        result = self._make_request("GET", endpoint)
        
        if "error" in result:
            return result
        
        issues = []
        for issue in result.get("issues", []):
            issues.append({
                "key": issue["key"],
                "type": issue["fields"].get("issuetype", {}).get("name", "Unknown"),
                "summary": issue["fields"].get("summary", ""),
                "status": issue["fields"].get("status", {}).get("name", "Unknown"),
                "assignee": issue["fields"].get("assignee", {}).get("displayName", "Unassigned") if issue["fields"].get("assignee") else "Unassigned",
                "priority": issue["fields"].get("priority", {}).get("name", "None") if issue["fields"].get("priority") else "None",
                "created": issue["fields"].get("created", ""),
                "updated": issue["fields"].get("updated", "")
            })
        
        return {
            "status": "success",
            "total": len(issues),
            "issues": issues
        }
