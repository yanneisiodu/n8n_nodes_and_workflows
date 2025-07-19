# n8n-nodes-amazon-nova-act

An n8n community node for Amazon Nova Act - AI-powered browser automation using natural language.

## Features

- **Browser Automation**: Control web browsers using natural language commands
- **Data Extraction**: Extract structured data from web pages using AI
- **Headless Support**: Run browsers in headless mode for production environments
- **Screenshot Capture**: Automatically capture screenshots for debugging and verification
- **Error Handling**: Robust error handling with detailed feedback

## Prerequisites

- Node.js 20.15 or higher
- Python 3.10 or higher
- Docker (recommended for deployment)
- Amazon Nova Act API key (get it from [nova.amazon.com/act](https://nova.amazon.com/act))

## Installation

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/n8n-nodes-amazon-nova-act.git
cd n8n-nodes-amazon-nova-act
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Build the node:
```bash
npm run build
```

4. Link the package for local development:
```bash
npm link
```

5. In your n8n installation directory, link the custom node:
```bash
npm link n8n-nodes-amazon-nova-act
```

### Docker Setup (Recommended)

1. Build and run with Docker Compose:
```bash
docker-compose up --build -d
```

2. Access n8n at `http://localhost:5678`
   - Username: `admin`
   - Password: `password`

## Configuration

### API Credentials

1. Go to [nova.amazon.com/act](https://nova.amazon.com/act) to get your API key
2. In n8n, create a new "Amazon Nova Act API" credential
3. Enter your API key

### Node Options

- **Starting URL**: Optional URL to start the browser session
- **Headless Mode**: Run browser without visible UI (recommended for production)
- **Session Timeout**: Maximum time to wait for automation completion
- **Commands**: Natural language commands to execute (for Perform Actions)
- **Data Schema**: JSON schema for data extraction (for Extract Data operation)
- **Navigation Commands**: Commands to navigate before extracting data

## Usage Examples

### Perform Browser Actions

```
Commands:
Go to https://example.com
Click the "Sign up" button
Fill in the email field with "test@example.com"
Fill in the password field with "securepassword"
Click the "Create Account" button
Take a screenshot
```

### Extract Structured Data

```
Starting URL: https://news.ycombinator.com
Data Schema:
{
  "stories": [
    {
      "title": "string",
      "points": "number",
      "comments": "number",
      "url": "string"
    }
  ]
}
Navigation Commands:
Scroll down to load more stories
Wait for the page to fully load
```

## Best Practices

1. **Break Down Complex Tasks**: Split complex automation into smaller, specific commands
2. **Use Descriptive Commands**: Be specific about what elements to interact with
3. **Handle Errors Gracefully**: Enable "Continue on Fail" for workflows that might encounter errors
4. **Test in Non-Headless Mode**: Turn off headless mode during development to see what's happening
5. **Secure API Keys**: Always use n8n credentials to store your Nova Act API key securely

## Limitations

- Amazon Nova Act is currently in research preview
- Available only in the US region
- Rate limits may apply based on your API plan
- Complex JavaScript interactions might not work reliably
- Performance may vary depending on website complexity

## Troubleshooting

### Common Issues

1. **"nova-act package not installed"**
   - Ensure Python dependencies are installed: `pip install -r requirements.txt`

2. **"API key invalid"**
   - Verify your API key at nova.amazon.com/act
   - Ensure the credential is properly configured in n8n

3. **Browser automation fails**
   - Try running in non-headless mode for debugging
   - Check if the website has anti-bot protection
   - Ensure commands are specific and clear

4. **Timeout errors**
   - Increase the session timeout value
   - Break down complex tasks into smaller steps

### Logs and Debugging

- Screenshots are saved to `/home/node/nova_screenshots` in the Docker container
- Logs are available in `/home/node/nova_logs`
- Enable debug mode by setting environment variable: `N8N_LOG_LEVEL=debug`

## Development

### Building

```bash
npm run build
```

### Linting

```bash
npm run lint
npm run lintfix  # Auto-fix issues
```

### Formatting

```bash
npm run format
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- [Amazon Nova Act Documentation](https://nova.amazon.com/act)
- [n8n Community Forum](https://community.n8n.io/)
- [GitHub Issues](https://github.com/yourusername/n8n-nodes-amazon-nova-act/issues)

## Disclaimer

This is an unofficial community node for Amazon Nova Act. It is not affiliated with or endorsed by Amazon. Amazon Nova Act is a research preview service and should be used accordingly.