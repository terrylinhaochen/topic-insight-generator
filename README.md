# AI Insight Generator

A web application that uses AI to generate insightful discussion topics and book recommendations for both career development and parenting domains. The system uses Claude to analyze user inputs and generate structured insights that connect everyday experiences to deeper patterns and unexpected domains.

## Project Overview

The application consists of:
- A FastAPI backend that handles prompt management and AI interactions
- A React frontend that provides a clean interface for users to input topics and view insights
- Integration with Claude AI for generating structured insights
- Domain-specific prompting systems for career and parenting topics

## File Structure

```
├── backend/
│   ├── config/
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── career.py
│   │   │   └── parenting.py
│   ├── utils/
│   │   └── prompt_handler.py
│   ├── .env
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── package-lock.json
└── README.md
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with your credentials:
```
CLAUDE_API_KEY=your_claude_api_key
FRONTEND_URL=http://localhost:3000
```

5. Start the backend server:
```bash
uvicorn main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The application should now be running at `http://localhost:3000`

## API Endpoints

### POST /api/generate/{domain}

Generates an insight for the specified domain (career or parenting).

Request body:
```json
{
  "content": "string"
}
```

Response:
```json
{
  "content": {
    "episodeTitle": "string",
    "description": "string",
    "books": {
      "primary": {
        "title": "string",
        "author": "string"
      },
      "supporting": [
        {
          "title": "string",
          "author": "string"
        }
      ]
    }
  },
  "timestamp": "string"
}
```

## Features

- Domain-specific insight generation for career and parenting topics
- Structured output with titles, descriptions, and book recommendations
- Clean, responsive user interface
- Error handling and loading states
- CORS support for local development

## Development Notes

- The backend uses FastAPI for its async capabilities and automatic OpenAPI documentation
- The frontend is built with React and uses modern hooks for state management
- The system uses environment variables for configuration
- CORS is configured to allow frontend-backend communication in development

## Error Handling

The application includes error handling for:
- Invalid domains
- Failed API requests
- Malformed responses
- Network issues

## Future Improvements

- Add user authentication
- Implement rate limiting
- Add caching for common queries
- Expand to additional domains
- Add testing suite
- Add logging system
- Deploy to production environment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Deployment

### Streamlit Cloud Deployment

To deploy the demo version on Streamlit Cloud:

1. Make sure your repository is public on GitHub
2. Create a `streamlit_app.py` in the root directory
3. Sign up for a Streamlit Cloud account
4. Connect your GitHub repository
5. Configure the following secrets in Streamlit Cloud:
   - CLAUDE_API_KEY
   - FRONTEND_URL
   - Other environment variables as needed

⚠️ **Security Considerations**

When making the repository public:
1. Ensure `.gitignore` is properly set up
2. Remove any sensitive information from commit history
3. Never commit `.env` files
4. Use environment variables for all sensitive data
5. Regularly audit your code for exposed credentials

### Local Development Security

For local development:
1. Keep `.env` files local and never commit them
2. Use the provided `.gitignore`
3. Regularly update dependencies
4. Follow security best practices for API key management

## License

This project is licensed under the MIT License - see the LICENSE file for details. 