# Azure DevOps Bug Tracker for GitHub Copilot Agent (MCP)

A complete solution that integrates GitHub Copilot Agent with Azure DevOps to fetch, analyze, and report bug data using the Model Context Protocol (MCP).

## 📁 Project Structure

```
azure-devops-copilot-bugs/
├── .vscode/
│   └── mcp.json                    # MCP server config for Copilot Agent
├── .github/
│   └── copilot-instructions.md     # Copilot Agent instructions
├── src/
│   ├── __init__.py
│   ├── config.py                   # Configuration & env management
│   ├── azure_devops_client.py      # REST API client with retry
│   └── bug_report_generator.py     # Multi-format report generator
├── output/                         # Generated reports
├── main.py                         # CLI entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
└── README.md                       # This file
```

## 🚀 Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ (for MCP server)
- VS Code with GitHub Copilot extension
- Azure DevOps account with PAT token

### Step 1: Clone and Install

```bash
cd azure-devops-copilot-bugs
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your values
```

Required variables:
| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_DEVOPS_ORG_URL` | Organization URL | `https://dev.azure.com/myorg` |
| `AZURE_DEVOPS_PAT` | Personal Access Token | `xxxxxxxxxxxxxxxxxxxxx` |
| `AZURE_DEVOPS_PROJECT` | Project name | `MyProject` |

### Step 3: Create Azure DevOps PAT

1. Go to Azure DevOps → User Settings → Personal Access Tokens
2. Click "New Token"
3. Set the following scopes:
   - **Work Items**: Read
   - **Project and Team**: Read
4. Copy the generated token to your `.env` file

### Step 4: Configure MCP Server (for Copilot Agent)

The `.vscode/mcp.json` file is pre-configured. Set environment variables in your system or VS Code settings:

**Option A: System Environment Variables (Recommended for production)**
```powershell
[System.Environment]::SetEnvironmentVariable("AZURE_DEVOPS_ORG_URL", "https://dev.azure.com/yourorg", "User")
[System.Environment]::SetEnvironmentVariable("AZURE_DEVOPS_PAT", "your-pat-token", "User")
[System.Environment]::SetEnvironmentVariable("AZURE_DEVOPS_PROJECT", "your-project", "User")
```

**Option B: VS Code Settings**
Add to your `.vscode/settings.json`:
```json
{
  "github.copilot.chat.mcpServers.env": {
    "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/yourorg",
    "AZURE_DEVOPS_PAT": "your-pat-token",
    "AZURE_DEVOPS_PROJECT": "your-project"
  }
}
```

## 🖥️ CLI Usage

```bash
# Fetch active bugs
python main.py --active

# Fetch P1 and P2 bugs
python main.py --p1p2

# Fetch my bugs
python main.py --my-bugs

# Fetch current sprint bugs
python main.py --sprint

# Fetch specific sprint bugs
python main.py --sprint "MyProject\\Sprint 15"

# Show bug statistics
python main.py --stats

# List saved queries
python main.py --saved-queries

# Export all bugs to all formats
python main.py --all --export all

# Export active bugs to HTML dashboard
python main.py --active --export html

# Export P1/P2 bugs to Excel
python main.py --p1p2 --export excel
```

## 🤖 GitHub Copilot Agent Prompts

Use these prompts in VS Code Copilot Chat (Agent Mode):

### Basic Queries

```
@workspace Show me all active bugs in Azure DevOps
```

```
@workspace List all P1 and P2 bugs with their assignees
```

```
@workspace What bugs are assigned to me?
```

```
@workspace Show bugs in the current sprint
```

### Dashboard & Reports

```
@workspace Generate a daily bug dashboard with statistics
```

```
@workspace Create a summary of sprint defects grouped by priority
```

```
@workspace Show bug trends by severity for the last 3 sprints
```

### Analysis

```
@workspace List all blocker bugs that are unassigned
```

```
@workspace Which team member has the most open bugs?
```

```
@workspace Show me the bug resolution rate for this sprint
```

```
@workspace Compare P1 bugs between current and previous sprint
```

### Reporting

```
@workspace Export all active bugs to an Excel file with priority highlighting
```

```
@workspace Generate an HTML bug dashboard for the team standup
```

```
@workspace Create a CSV of all bugs created this week
```

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `401 Unauthorized` | Check PAT token is valid and has correct scopes |
| `404 Not Found` | Verify organization URL and project name |
| `Connection timeout` | Check network/VPN connectivity to Azure DevOps |
| MCP server not starting | Ensure Node.js 18+ is installed, run `npx -y @anthropic/azure-devops-mcp-server` manually to test |
| `No bugs found` | Verify WIQL query syntax and project has bug work items |

### Verify PAT Token

```bash
curl -u :YOUR_PAT_TOKEN "https://dev.azure.com/yourorg/yourproject/_apis/wit/wiql?api-version=7.1" -H "Content-Type: application/json" -d "{\"query\": \"SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Bug' AND [System.State] = 'Active'\"}"
```

### Debug Logging

Set `LOG_LEVEL=DEBUG` in your `.env` file for verbose output:
```bash
LOG_LEVEL=DEBUG python main.py --active
```

### MCP Server Debugging

Test the MCP server connection:
```bash
npx -y @anthropic/azure-devops-mcp-server --help
```

Check VS Code Output panel → "GitHub Copilot Chat" for MCP connection logs.

## 📊 Report Outputs

| Format | Description | Use Case |
|--------|-------------|----------|
| CSV | Comma-separated values | Data import, spreadsheets |
| Excel | Formatted .xlsx with colors | Stakeholder reports |
| HTML | Interactive dashboard | Team standup, sharing |
| JSON | Structured data | API integration, automation |

## 🔐 Security Notes

- **Never commit** `.env` files or PAT tokens to source control
- Use environment variables or Azure Key Vault for production
- PAT tokens should have minimum required scopes (Work Items: Read)
- Rotate PAT tokens regularly (recommended: every 90 days)
- The `.gitignore` excludes sensitive files

## 📝 License

MIT License
