# Testing Agent - Automated Web Testing Tool

An AI-powered web testing tool that combines Selenium automation with Figma design validation.

## Features

- Automated web component testing
- Figma design validation
- Responsive design testing
- Screenshot comparison
- AI-powered test case generation
- Interactive test reports

## Prerequisites

- Python 3.12.0 or higher
- Google Chrome browser
- Figma API key
- Google Gemini API key
- macOS (for local development)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/therealdope/Testing_Agent_Backend
cd Testing_Agent_Backend
```

2. Create and activate virtual environment(MacOS):
```bash
python -m venv env
source env/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create .env file in the root directory:
```plaintext
GOOGLE_API_KEY=your_gemini_api_key
FIGMA_API_KEY=your_figma_api_key
FLASK_APP=app.py
FLASK_ENV=development
```

5. Run the application:
```bash
python app.py
```

The server will start at
 `http://localhost:5000`
or 
`http://127.0.0.1:5000`
 - In Frontend below link is used for Backend API URL `http://127.0.0.1:5000/testagent`

## Environment Setup

### Chrome Setup
1. Install Google Chrome if not already installed
2. Verify Chrome installation:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

### ChromeDriver Setup
The project uses webdriver-manager which automatically handles ChromeDriver installation.

### API Keys Setup
1. Get Figma API key from your Figma account settings
2. Get Google Gemini API key from Google AI Studio
3. Add both keys to your .env file

## Usage

1. Start the server:
```bash
python app.py
```

2. Access the web interface at
`http://localhost:5000`
or
`http://127.0.0.1:5000`

3. Enter:
   - Website URL to test
   - Figma file ID

4. View generated:
   - Generated Test File
   - Component Test log
   - Functional Test log
   - Responsive Testing log
   - Screenshots

## Project Structure

```
flask/
├── app.py              # Main Flask application
├── src.py             # Core testing logic
├── requirements.txt   # Python dependencies
├── templates/         # HTML templates
│   └── index.html    # Main interface
└── .env              # Environment variables
```

## Error Handling

If you encounter any issues:

1. Verify all environment variables are set correctly
2. Ensure Chrome is installed in the default location
3. Check Python version compatibility
4. Verify API keys are valid and have necessary permissions

## Development

To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
