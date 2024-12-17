# School Presentation Management System

A web application for managing company presentations at schools. Companies can register with a special access key and create presentations, while students can register and sign up for presentations.

## Features

- User authentication (students and companies)
- Company registration with access key
- Presentation creation and management
- Student registration for presentations

## Setup

1. Install Python 3.8 or higher

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Usage

### For Companies
1. Register as a company using the provided access key
2. Create presentations with title, description, and date/time
3. View registered students for your presentations

### For Students
1. Register as a student with your class information
2. Browse available presentations
3. Register for presentations you're interested in

## Security Note
The default access key for company registration is 'your_secret_key'. Make sure to change this in the production environment by modifying the value in app.py. 