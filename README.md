# SWE-5 Agentic Workflow

> **Automated Test Generation**: PlantUML Sequence Diagrams → IBM RQM Test Cases → Robot Framework Scripts

Transform PlantUML sequence diagrams into validated RQM test cases and executable Robot Framework scripts using GitHub Copilot AI agents with full end-to-end traceability.

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Quick Setup](#quick-setup)
3. [Usage](#usage)
   - [Quick Example](#quick-example)
   - [Common Prompts](#common-prompts)
4. [Test Case Setup in ETM](#test-case-setup-in-etm)
5. [Troubleshooting](#troubleshooting)
6. [About](#about)

---

## Overview

The SWE-5 Agentic Workflow automates the creation and maintenance of integration test cases through an AI-powered pipeline:

- **📊 Diagram Analysis**: Parse PlantUML sequence diagrams with 40+ built-in pattern recognition rules
- **🤖 Intelligent Generation**: Auto-generate RQM test cases with pre/post conditions and step-by-step test designs
- **✏️ Natural Language Editing**: Edit test cases via chat before committing to RQM
- **🔗 Full Traceability**: Bidirectional linking between diagrams, RQM test cases, and Robot Framework scripts
- **🔄 Smart Updates**: Detects changes and intelligently merges updates while preserving manual edits

### Key Features

- **Multi-flow detection** from single diagrams (1 diagram → N test cases)
- **Interactive editing** before RQM commit
- **Template-based generation** from similar existing tests
- **Automated Robot Framework script generation**
- **Source tracking** for change management

---

## Getting Started

### Prerequisites

- **Python 3.11+** with `uv` package manager
  ```bash
  pip install uv
  ```
- **VS Code** with latest GitHub Copilot extension
- **IBM RQM Access**: Valid credentials for your ETM/RQM server
- **Git** for version control

### Quick Setup

#### 1. Clone Repository

```bash
git clone <repository-url>
cd SWE-5-IT-Agent
```

#### 2. Configure MCP Server

Edit [.vscode/mcp.json](.vscode/mcp.json) and add your RQM credentials:

```json
{
  "servers": {
    "etm": {
      "command": "uv",
      "args": ["--directory", "etm", "run", "etmmcpserver.py"],
      "env": {
        "ETM_BASE_URL": "YOUR_ETM_BASE_URL",
        "ETM_USERNAME": "YOUR_USERNAME",
        "ETM_PASSWORD": "YOUR_PASSWORD",
        "ETM_PROJECT_AREA": "YOUR_PROJECT_AREA",
        "ETM_VERIFY_SSL": "false"
      }
    }
  }
}
```

**⚠️ Security Note**: Add `.vscode/` to `.gitignore` to protect credentials.

#### 3. Configure Project Settings

Edit [etm_project_config.json](etm_project_config.json) with your project details:

```json
{
  "project_area": "Your_Project_Area_Name",
  "default_test_plan_id": "YOUR_TEST_PLAN_ID",
  "test_plan_title": "Your_Test_Plan_Title",
  "configuration_context": "YOUR_CONFIGURATION_CONTEXT_URL"
}
```

#### 4. Install Dependencies

```bash
# Install ETM MCP Server
cd etm
uv sync

# Install Robot Framework libraries (optional)
cd ../robot/rfw_libraries
pip install -e .
```

#### 5. Verify Installation

```bash
cd etm
uv run pytest tests/test_connection_tools.py -v
```

---

## Usage

### Quick Example

**Generate test cases from a PlantUML diagram:**

```
@test-generator analyze examples/diagrams/RBM_Standby.puml
```

**What happens next:**

1. 🔍 **Analysis**: System detects test flows in your diagram
2. ✏️ **Naming**: You provide names for each detected flow
3. 📝 **Generation**: System creates test case with pre/post conditions and steps
4. 💬 **Interactive Editing**: Edit via natural language commands
5. ✅ **Finalize**: Type "done" to commit to RQM
6. 🤖 **Robot Script**: Optionally generate Robot Framework script

### Common Prompts

#### Main Workflow

```
@test-generator analyze <diagram-file-path>
```

#### Analyze Diagram Structure

```
@diagram-analyzer parse examples/test.puml
```

#### Update Existing Test Case

```
@rqm-uploader update test case <TEST_CASE_ID> from <diagram-path>
```

#### Generate Robot Framework Script

```
@rfw-generator create script from test case <TEST_CASE_ID>
```

#### Interactive Editing Commands

After preview is shown, use these commands:

```
change title to <new-title>
set priority to P1 / P2 / P3 / P4
add step after <N>: <step-description>
remove step <N>
change step <N> to <new-description>
add precondition: <condition>
add postcondition: <condition>
show preview
done
```

### Available Agents

| Agent | Purpose |
|-------|---------|
| **@test-generator** | Main orchestrator for end-to-end workflow |
| **@diagram-analyzer** | Parse PlantUML diagrams with pattern recognition |
| **@rqm-uploader** | Upload/update test cases in RQM |
| **@rfw-generator** | Generate Robot Framework test scripts |

---

## Test Case Setup in ETM

_This section will guide you through setting up test cases in your ETM/RQM project area._

### Step-by-Step Process

<!-- Images and detailed steps will be added here -->

**Prerequisites:**
- Access to ETM/RQM server
- Write permissions in your project area
- Test plan and test suite already created

**Setup Steps:**

1. **Create Custom Attributes** (for source tracking)
2. **Configure Categories** (ASIL rating, test level, etc.)
3. **Set Up Test Plan Structure**
4. **Define Component Mapping**
5. **Configure Architecture Element Links**

_Detailed instructions with screenshots coming soon..._

---

## Troubleshooting

### MCP Server Connection Failed

**Symptoms:** Cannot connect to ETM server

**Solutions:**
- Verify credentials in [.vscode/mcp.json](.vscode/mcp.json)
- Check `ETM_BASE_URL`, `ETM_USERNAME`, `ETM_PASSWORD` are correct
- Test connection: `cd etm && uv run pytest tests/test_auth.py -v`
- Verify network access to RQM server

### Agents Not Visible

**Symptoms:** Typing `@` doesn't show available agents

**Solutions:**
- Restart VS Code (close all windows)
- Verify agent files exist in [.github/agents](.github/agents/)
- Update GitHub Copilot extension
- Check YAML frontmatter syntax in agent files

### Authentication Errors (401 Unauthorized)

**Symptoms:** 401 error when calling RQM tools

**Solutions:**
- Try alternate username formats:
  - `ABD1XYZ` (plain NT ID)
  - `BOSCH\ABD1XYZ` (domain\user)
  - `ABD1XYZ@bosch.com` (email format)
- Verify password works in RQM web UI
- Check if account is locked (contact IT)

### Robot Framework Import Errors

**Symptoms:** Generated scripts have import errors

**Solutions:**
- Install libraries: `cd robot/rfw_libraries && pip install -e .`
- Verify resource files exist in `robot/rfw_resources/`
- Check platform-specific keyword availability (uP vs uC)

### Test Case Not Found

**Symptoms:** Cannot find existing test cases

**Solutions:**
- Verify test case ID is correct
- Check you have read permissions in project area
- Ensure test case is in the correct project area
- Try using test plan tree search as fallback

### XML Corruption After Update

**Symptoms:** Test case shows garbled HTML in RQM

**Solutions:**
- System automatically fixes XML after updates
- If still broken, the agent will auto-repair on next update
- Check ETM MCP server logs in `etm/logs/`

---

## About

**Project**: SWE-5 Integration Test Automation  
**Purpose**: Streamline test case creation from sequence diagrams  
**Technology Stack**:
- GitHub Copilot AI Agents
- IBM RQM/ETM (Engineering Test Management)
- PlantUML for sequence diagrams
- Robot Framework for test automation
- Python 3.11+ with MCP (Model Context Protocol)

### Workspace Structure

```
c:\SWE - 5 IT Agent\
├── .github/
│   ├── agents/              # 4 Copilot agents
│   │   ├── test-generator.agent.md      # Main orchestrator
│   │   ├── diagram-analyzer.agent.md    # PlantUML parser
│   │   ├── rqm-uploader.agent.md        # RQM integration
│   │   └── rfw-generator.agent.md       # Robot script gen
│   └── instructions/        # Agent instruction files
├── .vscode/
│   └── mcp.json            # MCP server configuration
├── etm/                    # ETM MCP server (52 RQM tools)
│   ├── etmmcpserver.py     # Server entry point
│   ├── core/               # Configuration
│   ├── tools/              # RQM operations
│   └── services/           # OSLC client
├── examples/               # Sample PlantUML diagrams
│   └── diagrams/          # Example sequence diagrams
├── robot/                  # Robot Framework files
│   ├── rfw_libraries/     # Custom libraries
│   └── rfw_resources/     # Resource files
├── etm_project_config.json # Project configuration
└── README.md              # This file
```

### Key Statistics

- **4 Specialized Agents** for modular workflow
- **55 RQM Operations** via ETM MCP Server
- **40+ Pattern Recognition Rules** for diagram analysis
- **Full Traceability** from diagram to executable test

---
