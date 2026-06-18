# GitHub Copilot Agent - Azure DevOps Bug Tracking Instructions

## Context

This project integrates with Azure DevOps to fetch and analyze bug work items. The Copilot Agent has access to the Azure DevOps MCP server for querying work items directly.

## Available Capabilities

- Connect to Azure DevOps organization via MCP server
- Execute saved WIQL queries from Azure DevOps
- Fetch bug work items with filtering (state, priority, assignee, sprint)
- Generate reports in CSV, Excel, HTML, and JSON formats
- Provide sprint-wise bug statistics and trends

## How to Use

### Fetching Bugs

When asked about bugs, use the Azure DevOps MCP tools to:

1. **Show all active bugs**: Query work items where `[System.WorkItemType] = 'Bug' AND [System.State] = 'Active'`
2. **Show P1/P2 bugs**: Filter by `[Microsoft.VSTS.Common.Priority] <= 2`
3. **Show my bugs**: Filter by `[System.AssignedTo] = @Me`
4. **Sprint bugs**: Filter by `[System.IterationPath]` for current sprint

### Sample WIQL Queries

```wiql
-- All Active Bugs
SELECT [System.Id], [System.Title], [System.State], [Microsoft.VSTS.Common.Priority], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] = 'Bug' AND [System.State] = 'Active'
ORDER BY [Microsoft.VSTS.Common.Priority] ASC

-- P1 and P2 Bugs
SELECT [System.Id], [System.Title], [System.State], [Microsoft.VSTS.Common.Priority], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] = 'Bug' AND [Microsoft.VSTS.Common.Priority] <= 2
ORDER BY [Microsoft.VSTS.Common.Priority] ASC

-- Bugs Assigned to Me
SELECT [System.Id], [System.Title], [System.State], [Microsoft.VSTS.Common.Priority]
FROM WorkItems
WHERE [System.WorkItemType] = 'Bug' AND [System.AssignedTo] = @Me
ORDER BY [System.State] ASC

-- Current Sprint Bugs
SELECT [System.Id], [System.Title], [System.State], [Microsoft.VSTS.Common.Priority], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] = 'Bug' AND [System.IterationPath] = @CurrentIteration
ORDER BY [Microsoft.VSTS.Common.Priority] ASC
```

### Generating Reports

When asked to generate reports or dashboards:
1. Fetch the relevant bug data using WIQL queries
2. Use the Python scripts in `src/` to generate formatted outputs
3. Reports are saved to the `output/` directory

### Response Format

When presenting bug data:
- Always include Bug ID, Title, Priority, State, and Assigned To
- Group by priority when showing multiple bugs
- Highlight P1 bugs as critical/blockers
- Include counts and summaries at the top of listings

## Project Structure

- `src/config.py` - Configuration and environment variables
- `src/azure_devops_client.py` - Azure DevOps REST API client
- `src/bug_report_generator.py` - Report generation (CSV, Excel, HTML, JSON)
- `src/main.py` - CLI entry point
- `.vscode/mcp.json` - MCP server configuration for Copilot Agent
- `output/` - Generated reports directory

## Environment Variables Required

- `AZURE_DEVOPS_ORG_URL` - Organization URL (e.g., https://dev.azure.com/yourorg)
- `AZURE_DEVOPS_PAT` - Personal Access Token
- `AZURE_DEVOPS_PROJECT` - Project name
