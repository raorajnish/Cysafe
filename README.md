# CySafe - Cyber Security Awareness Platform

CySafe is a Django-based web application designed to raise awareness about cyber crimes and provide educational content about cybersecurity threats and prevention measures.

## Features

- **Cyber Crime Database**: Comprehensive collection of cyber crimes with detailed descriptions
- **Trending Crimes**: Display of most viewed cyber crimes
- **Educational Content**: Detailed information about various types of cyber attacks
- **Interactive Learning**: Click tracking for popular content
- **Responsive Design**: Modern, mobile-friendly interface
- **Admin Panel**: Easy content management through Django admin

## Technology Stack

- **Backend**: Django 4.2.7
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Authentication**: Django Allauth
- **Forms**: Django Crispy Forms with Bootstrap 5
- **API**: Django REST Framework

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/raorajnish/Cysafe.git
   cd Cysafe/CySafe-Django
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   
   **Windows:**
   ```bash
   venv\Scripts\activate
   ```
   
   **macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Project Structure

```
CySafe-Django/
├── cysafe_project/          # Django project settings
├── main/                    # Main application
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── urls.py             # URL routing
│   └── admin.py            # Admin interface
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   └── main/              # App-specific templates
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── logs/                  # Application logs
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Key Features

### Cyber Crime Tracking
- View count tracking for educational content
- Trending crimes based on user engagement
- Detailed crime descriptions and prevention tips

### Admin Features
- Add/edit cyber crimes through admin panel
- Manage user accounts and permissions
- View analytics and engagement metrics

### User Interface
- Modern, responsive design
- Interactive elements with JavaScript
- Bootstrap 5 for styling
- Font Awesome icons

## API Endpoints

- `POST /api/increment-clicks/` - Increment view count for a crime
- `GET /crime/<id>/` - View detailed crime information
- `GET /crimes/` - List all cyber crimes
- `GET /` - Home page with trending crimes

## Contributors

**CyberSafe Team**

| Name | Role |
|------|------|
| **Rajnish Rao** | Project Lead & Full Stack Developer |
| **Omkar Wayal** | UI/UX Designer |
| **Sahil Rane** | Frontend Developer |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue on the GitHub repository.

## Recent Updates

- Fixed view count incrementing issue (was incrementing by 2-3 instead of 1)
- Added debounce mechanism to prevent rapid clicking
- Centralized click tracking logic
- Improved code organization and documentation 