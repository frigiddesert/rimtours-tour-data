# RimTours Tour Data Integration

## Overview
Complete data synchronization system for RimTours between Arctic reservation system, WordPress ACF fields, and Outline documentation.

## Features
- Arctic-first data synchronization
- ACF field mapping from WordPress export
- Outline API integration
- PostgreSQL database management
- Bidirectional sync capabilities
- Appsmith dashboard automation

## Architecture
- Arctic system: Primary source of truth for pricing/configurations
- WordPress ACF: Rich content and descriptions
- Outline: Documentation system
- PostgreSQL: Central data hub
- Appsmith: Automation and management interface

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Configure environment variables
3. Set up PostgreSQL database
4. Configure API keys

## Directory Structure
```
rimtours-tour-data/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── input/          # Source data files
│   └── output/         # Generated unified data
├── scripts/            # Python scripts for processing
├── appsmith/          # Appsmith dashboard configs
├── api/               # API integration scripts
├── tests/             # Test files
└── docs/              # Documentation
```

## Components
- **Data Unification**: Merges Arctic and WordPress ACF data
- **Markdown Generation**: Creates Outline-ready documentation
- **PostgreSQL Sync**: Central data storage and management
- **Outline API**: Direct integration with Outline
- **Appsmith Dashboards**: Visual automation interface