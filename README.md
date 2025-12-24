# Time Left - ChatGPT App

A simple ChatGPT app that shows elegant progress bar visualizations of how much time is left in the current day, week, month, and year.

## Features

- **Single Tool**: `get_time_remaining` - answers "how much time is left?" queries
- **Visual Progress Bars**: Animated, color-coded bars for each time period
- **Light/Dark Theme**: Automatically matches ChatGPT's theme
- **Real-time Calculation**: Shows current elapsed/remaining percentages

## Running Locally

```bash
cd server
uv run main.py
```

The server will start on `http://localhost:8000`.

## Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector@latest http://localhost:8000/mcp
```

## Testing in ChatGPT

1. Start the server locally
2. Expose it with ngrok: `ngrok http 8000`
3. In ChatGPT: Settings → Apps & Connectors → Advanced settings → Enable developer mode
4. Create a connector with your ngrok URL
5. Ask: "How much time is left?" or "What's my time progress?"

## Project Structure

```
time-left-chatgpt-app/
├── server/
│   ├── main.py           # MCP server with get_time_remaining tool
│   └── requirements.txt
├── web/
│   └── widget.html       # Progress bar visualization widget
└── README.md
```
