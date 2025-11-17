# Macro Mojo

Macro Mojo is a full-stack nutrition tracking web application that helps users 
set calorie and macronutrient goals, log meals, and monitor daily progress. It
includes authentication, database persistence, data validation, and an 
AI-powered assistant for personalized nutrition targets advice.

## Tech Stack

* **Backend Framework:** Python, Flask, psycopg2
* **Database:** PostgreSQL
* **AI Integration:** LangChain framework with multi-prompt routing, 
    conversation memory, ChatOpenAI (GPT-4) 
* **Frontend:** HTML, CSS, Jinja2 templates, embedded JavaScript
* **Environment & Dependency Management:** Poetry
* **Security & Authentication:** Input validation, SQL query sanitation, 
            protected routes, session-based authentication, bcrypt password
            hashing
* **Testing:** Pytest
* **Containerization:** Docker, Docker Compose


## Features

* User authentication with session management and bcrypt password hashing
* Relational database with normalized schema
* Full CRUD functionality for nutrition records
* SQL queries sanitization and input validation to prevent injection attacks
* Modular architecture for maintainability and future scalability
* AI assistant for personalized nutrition recommendations. 

## Installation & Setup

### Prerequisites
- Docker
- Docker Compose
- OpenAI API key 

### Quick Start

1. **Clone the repository**
```sh
git clone https://github.com/masyago/macro-mojo
cd macro_mojo
```

2. **Create environment files**
   Copy the example files to create your local configuration.
```sh
cp .env.example .env
cp db/password.txt.template db/password.txt
```
    
3. **Update secrets and API keys**
   * Edit `db/password.txt` to add your password.
   * Edit `.env` to replace `"your-open-ai-api-key"` with your OpenAI API key. 

4. **Build and run the application**

```sh
docker compose up --build
```

5. **Access the application**
   * Navigate to `http://localhost:5003/`
   * Development Credentials
    ```
    Username: `test_user`
    Password: `test_pwd`
    ```

## Stopping the Application
```sh
docker compose down
```
## Application Screenshots 

### Login

<img src="./screenshots/login.png" alt="Login Page" style="width:30%; height:auto;">

### Dashboard

<img src="./screenshots/dashboard.png" alt="Dashboard" style="width:40%; height:auto;">



### New Entries, Targets, Launch AI Assistant

<img src="./screenshots/demo.gif" alt="App Walkthrough" style="width:40%; height:auto;">


### AI Assistant

AI assistant provides advice on calories and macronutrient targets based on 
user details (age, sex, weight, height, activity level) and their goals (e.g.
lose weight, gain weight, gain muscle).

* Click 'Clear Char History' to delete ongoing conversation and start over

<img src="./screenshots/ai_assistant.png" alt="AI Assistant" style="width:40%; height:auto;">

## Development Roadmap

### Tech Enhancements

* **Security:** CSRF protection implementation (Flask-WTF)
* **ORM Integration:** Migrate to SQLAlchemy
* **Cloud Deployment:** Production deployment on Render
* **AI Framework:** Migration to LangChain v1.0
* **Performance:** Caching layer and database connection pooling

### Feature Expansions
* **Data Analytics:** Trend analysis
* **Weight Tracking**

## License
MIT


## Version History

* **0.1.1:** Added Docker and Docker Compose for containerization
* **0.1.0:** Initial release

**Last Updated:** November 2025




