# Quick Setup Guide: Project Manager Agent

## Prerequisites
- Python 3.8+
- Active Jira account
- Existing backend and UI setup

## Step 1: Install Dependencies
```bash
pip install requests
```

## Step 2: Generate Jira API Token
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. Name it (e.g., "AI Agent")
4. **Copy the token** (you won't see it again!)

## Step 3: Configure Environment Variables
Add to your `.env` file:
```bash
# Jira Configuration
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=paste-your-token-here
```

**Important**: 
- Replace `your-company` with your actual Jira domain
- Use your Jira login email for `JIRA_USERNAME`
- Paste the API token you just generated

## Step 4: Restart Backend
```bash
# Stop the current backend (Ctrl+C)
# Start it again
python main.py
```

## Step 5: Test the Agent

### In the UI:
1. Select **"📊 Project Manager Agent"** from the dropdown
2. Try these queries:

**Test 1: List Your Epics**
```
List all epics assigned to me
```

**Test 2: View Epic Stories**
```
Show me stories in epic PROJ-123
```
(Replace PROJ-123 with an actual epic key from your Jira)

**Test 3: Update Story**
```
Update story PROJ-456 status to In Progress
```
(Replace PROJ-456 with an actual story key)

## Troubleshooting

### Error: "JIRA_URL must be provided"
- Check your `.env` file has `JIRA_URL` set
- Restart the backend after adding it

### Error: "HTTP Error 401: Unauthorized"
- Verify `JIRA_USERNAME` is your Jira email
- Regenerate API token and update `.env`
- Make sure there are no extra spaces in the values

### Error: "HTTP Error 403: Forbidden"
- You don't have permission to access that epic/story
- Try with an epic/story you're assigned to

### Error: "HTTP Error 404: Not Found"
- The epic/story key doesn't exist
- Check the key format (e.g., PROJ-123)
- Verify you have access to that project

## Example Queries

### View Your Work
```
What epics are assigned to me?
List my assigned epics
Show me my epics
```

### Epic Details
```
Show details of epic PROJ-123
What's the status of epic PROJ-123?
How many stories are in epic PROJ-123?
```

### Story Information
```
Show stories in epic PROJ-123
What's the status of story PROJ-456?
List all stories in PROJ-123 and their statuses
```

### Update Stories
```
Update story PROJ-456 status to Done
Change PROJ-456 status to In Progress
Mark story PROJ-456 as Done
Assign story PROJ-456 to john.doe
Add comment to PROJ-456: "Completed implementation"
```

### Search
```
Find all high priority stories assigned to me
Search for stories in progress in project PROJ
Show all bugs in project PROJ
```

## Security Notes

1. **Never commit `.env` file** - It contains your API token
2. **Rotate tokens regularly** - Generate new tokens periodically
3. **Use read-only tokens if possible** - Limit permissions to what's needed
4. **Don't share tokens** - Each user should have their own token

## What the Agent Can Do

✅ **Read Operations:**
- List epics assigned to you
- View epic details
- List stories in an epic
- View story details
- Search issues with JQL

✅ **Update Operations:**
- Update story status
- Change story assignee
- Update story description
- Add comments to stories

❌ **Cannot Do (By Design):**
- Create epics or stories
- Delete epics or stories
- Modify epic details
- Change project settings

## Next Steps

Once working, you can:
1. Switch between Developer, DevOps, and Project Manager agents in the same session
2. Use PM agent to check tasks, then switch to Developer agent to implement them
3. Update Jira after completing work using PM agent

Enjoy your new Project Manager Agent! 🎉
