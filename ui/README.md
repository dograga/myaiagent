# Developer Assistant UI

A modern React + TypeScript chat interface for the Developer Assistant AI Agent.

## Features

- 💬 Real-time chat interface
- 🔄 Session management with history
- 🧠 Toggle thought process visibility
- 📝 Syntax highlighting for code
- 🎨 Beautiful, responsive design
- ⚡ Fast and lightweight (Vite)

## Setup

### Prerequisites

- Node.js 16+ and npm
- FastAPI backend running on `http://localhost:8000`

### Installation

```bash
cd ui
npm install
```

### Development

```bash
npm run dev
```

The UI will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Usage

1. **Start the FastAPI backend** (from the project root):
   ```bash
   uvicorn main:app --reload
   ```

2. **Start the UI** (from the ui directory):
   ```bash
   npm run dev
   ```

3. **Open your browser** to `http://localhost:3000`

## Features Guide

### Session Management

- **New Session**: Create a fresh conversation
- **Clear History**: Remove all messages from current session
- **Reload History**: Fetch the full conversation history from the server

### Thought Process

Toggle "Show Thought Process" to see:
- Actions the agent took
- Inputs to each action
- Results from each operation
- The agent's reasoning

### Chat Interface

- Type your query in the input field
- Press Enter or click Send
- View the agent's response with optional thought process
- Continue the conversation - the agent remembers context

## Example Queries

```
Create a Python file called calculator.py with add and subtract functions
```

```
Read the contents of main.py
```

```
Add a multiply function to calculator.py
```

```
List all Python files in the current directory
```

## Configuration

The UI connects to the FastAPI backend via proxy configuration in `vite.config.js`:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```

To change the backend URL, modify the `target` in `vite.config.js`.

## Troubleshooting

### Backend Connection Issues

If you see connection errors:
1. Ensure the FastAPI backend is running on port 8000
2. Check CORS is enabled in the backend
3. Verify the proxy configuration in `vite.config.js`

### Session Errors

If sessions aren't working:
1. Check the backend health endpoint: `http://localhost:8000/health`
2. Ensure GCP credentials are configured
3. Try creating a new session

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **CSS3** - Styling with animations
