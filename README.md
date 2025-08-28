# Support Ticket Automation System

An AI-powered support ticket automation system that processes messages from Google Chat, analyzes them using LangChain and Google Gemini 1.5, and creates tickets in ServiceNow.

## Features

- 🤖 **AI-powered message classification** - Automatically identifies support requests
- 📝 **Intelligent ticket summarization** - Creates clear, professional ticket summaries
- 🏷️ **Automated categorization** - Categorizes and prioritizes tickets
- 🎫 **ServiceNow integration** - Creates and tracks tickets in ServiceNow
- 💬 **Google Chat integration** - Processes messages and sends notifications
- ⏱️ **Scheduled workflows** - Runs periodic checks and updates

## Architecture

The system uses a multi-agent architecture built with LangGraph:

1. **Message Fetcher** - Retrieves messages from Google Chat
2. **Classifier Agent** - Determines if a message is a support request
3. **Summary Agent** - Creates structured ticket summaries
4. **Category Extractor** - Categorizes and prioritizes tickets
5. **ServiceNow Agent** - Creates tickets in ServiceNow
6. **Notification Agent** - Sends updates back to Google Chat
7. **Tracker Agent** - Monitors ticket status changes

## Project Structure

```
support_ticket_automation/
├── api/                  # API integrations
│   ├── google_chat.py    # Google Chat API
│   ├── servicenow.py     # ServiceNow API
│   └── webhook.py        # Webhook handler
├── agents/               # LLM agents
│   ├── classifier.py     # Message classifier
│   ├── summarizer.py     # Ticket summarizer
│   └── categorizer.py    # Category extractor
├── workflow/             # LangGraph workflow
│   ├── nodes.py          # Workflow nodes
│   └── graph.py          # Workflow graph
├── utils/                # Utilities
│   ├── credentials.py    # Credentials manager
│   ├── models.py         # Data models
│   └── scheduler.py      # Scheduler service
├── tests/                # Test utilities
│   └── test_utils.py     # Test data generator
├── main.py               # Main application
├── requirements.txt      # Dependencies
└── .env.template         # Environment template
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- Google Cloud account with Chat API enabled
- ServiceNow instance with API access
- Google Gemini API key

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd support-ticket-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.template .env
# Edit .env with your credentials
```

### 3. Configuration

See the [credentials_setup_guide.md](../credentials_setup_guide.md) for detailed instructions on setting up all required credentials.

### 4. Running the Application

```bash
# Generate environment template
python main.py --mode setup

# Run tests
python -m tests.test_utils

# Start server
python main.py --mode server --port 8000
```

## Webhook Endpoints

- **Google Chat**: `/webhook/google-chat` - Receives messages from Google Chat
- **ServiceNow**: `/webhook/servicenow` - Receives ticket updates from ServiceNow
- **Health Check**: `/health` - Server health check endpoint

## Development

### Adding New Features

1. **New Agent**: Add a new agent class in the `agents/` directory
2. **New Workflow Node**: Add a new node function in `workflow/nodes.py`
3. **Update Workflow Graph**: Update the graph in `workflow/graph.py`

### Testing

Run the test utilities to verify the system is working correctly:

```bash
python -m tests.test_utils
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
