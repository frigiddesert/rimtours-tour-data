# RimTours Data Integration Setup Guide

## Prerequisites

### System Requirements
- Python 3.8+
- PostgreSQL 12+
- Git
- GitHub CLI (gh)

### Required Accounts
- Arctic system API access
- Outline API access
- PostgreSQL database access

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/rimtours-tour-data.git
cd rimtours-tour-data
```

### 2. Set up Python Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Database Setup
1. Create PostgreSQL database
2. Run the database schema:
```bash
psql -d your_database_name -f database_schema.sql
```

### 4. Environment Configuration
Create a `.env` file in the root directory:

```env
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_DB=rimtours_data
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# Outline API Configuration
OUTLINE_API_KEY=your_outline_api_key
OUTLINE_URL=https://your-outline-instance.com/api
OUTLINE_DAY_TOURS_COLLECTION_ID=your_collection_id
OUTLINE_COLORADO_COLLECTION_ID=your_collection_id
OUTLINE_ARIZONA_COLLECTION_ID=your_collection_id
OUTLINE_UTAH_COLLECTION_ID=your_collection_id
OUTLINE_RENTALS_COLLECTION_ID=your_collection_id

# Arctic API Configuration
ARCTIC_API_KEY=your_arctic_api_key
ARCTIC_URL=https://your-arctic-system.com/api
```

### 5. Data Source Setup
Place your data files in the `data/input/` directory:
- `website_export.csv` - WordPress export with ACF fields
- `arctic_triptype.csv` - Arctic system tour data
- `arctic_pricing_final.csv` - Arctic pricing data

## Usage

### 1. Daily Sync Process
```bash
python scripts/sync_system.py
```

### 2. Manual Sync Operations
```python
from scripts.sync_system import RimToursDataSync

sync_system = RimToursDataSync()

# Individual sync operations
sync_system.sync_arctic_to_postgres()
sync_system.sync_wordpress_to_postgres()
sync_system.sync_postgres_to_outline()
sync_system.sync_outline_changes_to_arctic()

# Complete daily sync
sync_system.daily_sync()
```

### 3. Appsmith Integration
The system is designed to work with Appsmith for:
- Dashboard creation
- Data visualization
- Automation workflows
- Change management

## Directory Structure

```
rimtours-tour-data/
├── README.md
├── requirements.txt
├── .env (not tracked by Git)
├── database_schema.sql
├── data/
│   ├── input/          # Source data files
│   └── output/         # Generated unified data
├── scripts/
│   └── sync_system.py  # Main integration script
├── appsmith/          # Appsmith configuration files
├── api/               # API integration modules
├── tests/             # Test files
└── docs/              # Documentation
```

## Automation

### Cron Job Setup
Add to your crontab for daily sync:
```bash
# Run daily sync at 2 AM
0 2 * * * cd /path/to/rimtours-tour-data && source venv/bin/activate && python scripts/sync_system.py
```

## Troubleshooting

### Common Issues
1. **API Key Issues**: Verify all API keys are correct in `.env`
2. **Database Connection**: Check PostgreSQL connection settings
3. **File Permissions**: Ensure data files are readable

### Logging
The system logs all operations to help with debugging.

## Security

- API keys are stored in environment variables
- Database credentials are in environment variables
- Sensitive data is not committed to Git
- Use strong passwords for database access

## Backup Strategy

- Regular PostgreSQL database backups
- Version control for code and configuration
- Archive data files periodically