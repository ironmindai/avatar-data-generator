# Avatar Data Generator

> Enterprise-grade synthetic avatar generation platform powered by AI

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

**Avatar Data Generator** is a sophisticated web application that generates realistic synthetic avatars with complete biographical data, social media profiles, and authentic-looking images. Designed for AI practitioners, developers, and researchers who need high-quality synthetic persona data for testing, training, or demonstrations.

---

## 🌟 Features

### Core Capabilities
- **AI-Powered Persona Generation** - Generate realistic personas with complete demographic details (name, age, ethnicity, occupation, interests)
- **Multi-Platform Bios** - Automatic bio generation for Facebook, Instagram, X (Twitter), and TikTok with platform-specific styles
- **Image Generation Pipeline** - Integration with ComfyUI and SeeDream for authentic-looking avatar images
- **Batch Processing** - Generate 10-300 personas per task with configurable images per persona (4 or 8)
- **Multi-Language Support** - Generate bios in 100+ languages including native script support
- **Advanced Image Processing** - Automatic image degradation, EXIF obfuscation, and style randomization for authenticity

### User Interface
- **Modern Dashboard** - Charcoal & neon developer-focused aesthetic
- **Real-Time Progress Tracking** - Live updates during generation with detailed statistics
- **Dataset Management** - Browse, filter, and export generated datasets
- **Workflow Logs** - Detailed LLM workflow execution logs with token usage and cost tracking
- **Settings Panel** - Configurable generation parameters and image processing options

### Data Export
- **Multiple Formats** - Export as JSON, CSV, or ZIP (with images)
- **S3 Storage** - Automatic image upload to MinIO/S3-compatible storage
- **Structured Output** - Clean, well-organized data ready for immediate use

---

## 🏗️ Architecture

### Technology Stack
- **Backend**: Flask (Python 3.12)
- **Database**: PostgreSQL 16
- **Storage**: MinIO (S3-compatible)
- **Image Generation**: ComfyUI + SeeDream
- **LLM Integration**: OpenAI GPT-4 + Custom Workflow System
- **Task Queue**: Background scheduler with parallel processing
- **Frontend**: Vanilla JavaScript + Jinja2 templates

### Key Components
```
avatar-data-generator/
├── app.py                    # Flask application & routes
├── models.py                 # SQLAlchemy database models
├── services/
│   ├── comfyui_service.py   # ComfyUI integration
│   ├── s3_service.py        # S3/MinIO storage
│   ├── exif_service.py      # EXIF metadata manipulation
│   └── workflow_executor.py # LLM workflow engine
├── workflows/
│   └── persona_creation/    # Multi-step LLM workflows
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS, JavaScript, images
├── migrations/              # Alembic database migrations
└── docs/                    # Documentation
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 16+
- MinIO or S3-compatible storage
- OpenAI API key
- ComfyUI server (optional, for image generation)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd avatar-data-generator
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Set up database**
```bash
# Create PostgreSQL database
createdb avatar_data_generator

# Run migrations
flask db upgrade
```

6. **Start the application**
```bash
# Development
python app.py

# Production (with Gunicorn)
gunicorn --bind 0.0.0.0:8085 --workers 1 --threads 2 --timeout 120 app:create_app()
```

7. **Access the application**
```
http://localhost:8085
Default credentials: admin@example.com / admin123
```

---

## 📖 Usage

### Generating Avatars

1. **Navigate to Generate Avatars** (`/generate`)
2. **Configure generation**:
   - Persona Description: Describe your target demographic
   - Bio Language: Select from 100+ supported languages
   - Number to Generate: 10-300 personas
   - Images per Persona: 4 or 8 images
3. **Click "Generate Avatars"**
4. **Monitor progress** in real-time on the task detail page

### Viewing Datasets

1. **Navigate to Datasets** (`/datasets`)
2. **Click on a task** to view details
3. **Browse generated personas** with pagination
4. **Export data** as JSON, CSV, or ZIP

### Configuration Options

Access **Settings** (`/settings`) to configure:
- **Face Generation**: Randomization, cropping, style variations
- **Image Degradation**: Authentic photo effects (backlighting, flash, grain, etc.)
- **EXIF Metadata**: Obfuscation with randomized camera/GPS data
- **Bio Prompts**: Customize AI prompts for each social platform
- **Display Options**: Show/hide base reference images

---

## 🗄️ Database Schema

### Core Tables
- **users** - Authentication and user management
- **generation_tasks** - Batch generation jobs
- **generation_results** - Individual personas
- **workflow_logs** - LLM execution tracking
- **workflow_node_logs** - Detailed node execution logs
- **config** - Boolean application settings
- **int_config** - Integer application settings
- **settings** - Text-based settings (bio prompts)

### Migrations
Database schema is managed with Alembic. All migrations are in `migrations/versions/`.

---

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/avatar_data_generator

# Application
SECRET_KEY=your_secret_key_here
FLASK_ENV=production

# OpenAI
OPENAI_API_KEY=sk-...

# S3 Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=avatar-images
S3_REGION=us-east-1

# Optional
MULTITHREAD_FLOWISE=5
WORKER_INTERVAL=5
```

### Application Settings

Configure in **Settings** UI or directly in database:
- `crop_white_borders` - Auto-crop white borders (default: False)
- `randomize_image_style` - Apply random style variations (default: False)
- `randomize_face_base` - Random face generation (default: False)
- `obfuscate_exif_metadata` - Strip and inject fake EXIF data (default: False)
- `show_base_images` - Display base images in UI (default: True)
- `max_concurrent_tasks` - Parallel processing limit (default: 1)

---

## 📊 Workflow System

The application uses a custom **LLM Workflow Engine** for multi-step persona generation:

1. **Persona Creation** - Generate base demographic details
2. **Bio Generation** - Create platform-specific bios
3. **About Section** - Generate rich "About Me" content
4. **Image Ideas** - Generate creative prompts for image generation

Each workflow step is logged with:
- Execution time
- Token usage (prompt + completion)
- Cost calculation
- Input/output data
- Model configuration

View detailed logs at `/workflow-logs`.

---

## 🎨 Image Generation

### Pipeline
1. **Base Image Generation** - ComfyUI generates base portrait
2. **Image Splitting** - Create 4 or 8 variations
3. **Degradation** (optional) - Apply authentic photo effects
4. **EXIF Obfuscation** (optional) - Strip debug data, inject fake metadata
5. **S3 Upload** - Store with organized folder structure

### Degradation Effects
- Backlighting
- Flash problems
- Overexposure
- Low light / grain
- Old camera quality
- Focus issues
- White balance problems

Enable/disable specific effects in **Settings > Image Degradation**.

---

## 🔐 Security

- **Authentication** - Session-based login system
- **CSRF Protection** - All forms protected with CSRF tokens
- **Environment Variables** - Sensitive data in `.env` (never committed)
- **SQL Injection Protection** - SQLAlchemy ORM with parameterized queries
- **Input Validation** - Server-side validation on all inputs

---

## 📝 API Documentation

See `docs/backend-routes.md` for complete API documentation.

### Key Endpoints

**Authentication**
- `POST /login` - User login
- `GET /logout` - User logout

**Generation**
- `POST /generate` - Start generation task
- `GET /datasets/<task_id>/data` - Get task data with pagination

**Settings**
- `GET /settings` - Load settings UI
- `POST /settings/save` - Save configuration

**Export**
- `GET /datasets/<task_id>/export/json` - Export as JSON
- `GET /datasets/<task_id>/export/csv` - Export as CSV
- `GET /datasets/<task_id>/export/zip` - Export as ZIP with images

---

## 🛠️ Development

### Running Tests
```bash
pytest
```

### Database Migrations
```bash
# Create new migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Code Style
- Python: Follow PEP 8
- JavaScript: ES6+, functional style
- CSS: BEM naming convention
- Templates: Jinja2 with consistent indentation

---

## 📚 Documentation

- **Brandbook**: `docs/brandbook.md` - Design system and UI guidelines
- **Backend Routes**: `docs/backend-routes.md` - API documentation
- **Database Schema**: `docs/database-schema-manager.md` - Schema documentation
- **Web Templates**: `docs/webui-templates-index.md` - Template documentation
- **Generation Pipeline**: `docs/generation-pipeline.md` - Visual pipeline diagram

---

## 🤝 Contributing

This is a proprietary project. For access or contribution inquiries, contact the project maintainers.

---

## 📄 License

Proprietary - All Rights Reserved

---

## 🙏 Credits

**Developed by**: Galacticos AI
**Powered by**: OpenAI GPT-4, ComfyUI, SeeDream
**Built with**: Claude Code (Anthropic)

---

## 📞 Support

For issues, questions, or feature requests:
- Check `docs/` for detailed documentation
- Review workflow logs at `/workflow-logs`
- Monitor system logs with `journalctl -u avatar-data-generator`

---

**Last Updated**: February 2026
**Version**: 1.0.0
