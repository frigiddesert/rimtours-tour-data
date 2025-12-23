# Appsmith Integration Configuration

## Data Sources Setup

### PostgreSQL Connection
- **Type**: PostgreSQL
- **Connection**: 
  - Host: `{{secrets.POSTGRES_HOST}}`
  - Database: `{{secrets.POSTGRES_DB}}`
  - Username: `{{secrets.POSTGRES_USER}}`
  - Password: `{{secrets.POSTGRES_PASSWORD}}`

### Outline API Connection
- **Type**: REST API
- **Base URL**: `{{secrets.OUTLINE_URL}}`
- **Headers**:
  - Authorization: `Bearer {{secrets.OUTLINE_API_KEY}}`
  - Content-Type: `application/json`

### Arctic API Connection
- **Type**: REST API
- **Base URL**: `{{secrets.ARCTIC_URL}}`
- **Headers**:
  - Authorization: `Bearer {{secrets.ARCTIC_API_KEY}}`
  - Content-Type: `application/json`

## Appsmith Applications

### 1. Sync Dashboard Application

#### Queries:
```sql
-- Get all tours with sync status
SELECT 
    t.id,
    t.master_name,
    t.shortname as arctic_shortname,
    t.arctic_sync_status,
    a.price as arctic_price,
    w.subtitle,
    w.region,
    w.last_synced,
    CASE 
        WHEN a.price != w.pricing_info THEN 'CONFLICT'
        ELSE 'SYNCED'
    END as pricing_status
FROM tours t
LEFT JOIN (
    SELECT DISTINCT ON (tour_id) tour_id, price
    FROM arctic_data ORDER BY tour_id, updated_at DESC
) a ON t.id = a.tour_id
LEFT JOIN website_data w ON t.id = w.tour_id
ORDER BY t.arctic_sync_status, t.master_name
```

#### Widgets:
1. **Sync Status Card**
   - Shows total tours, synced tours, conflicts
   - Uses PostgreSQL query above

2. **Tours Table**
   - Displays all tours with sync status
   - Columns: Name, Arctic Code, Status, Last Updated
   - Actions: View details, Force sync

3. **Sync Control Buttons**
   - "Run Arctic → Outline Sync"
   - "Run Outline → Arctic Sync"
   - "Run Daily Sync"

4. **Status Indicator**
   - Shows last sync time
   - Color-coded by status

### 2. Data Viewer Application

#### Queries:
```sql
-- Filtered tour data
SELECT * FROM tours 
WHERE master_name ILIKE '%{{Input1.text}}%'
ORDER BY {{Dropdown1.selectedOptionValue}} {{Dropdown2.selectedOptionValue}}
LIMIT {{Slider1.value}}
```

#### Widgets:
1. **Search Input**: Filter tours by name
2. **Data Table**: Display filtered results
3. **Export Button**: CSV export functionality
4. **Refresh Button**: Update data from PostgreSQL

### 3. Change Management Application

#### Queries:
```sql
-- Get pending sync requests
SELECT * FROM sync_requests 
WHERE status = 'pending_review'
ORDER BY request_date DESC
```

#### Widgets:
1. **Pending Changes Table**
2. **Approve/Reject Buttons**
3. **Change Details Modal**
4. **Bulk Action Controls**

## Automation Workflows

### Scheduled Actions:
1. **Daily Sync**: Runs at 2 AM automatically
2. **Conflict Detection**: Runs hourly to detect conflicts
3. **Status Reports**: Runs weekly with sync summary

### Webhook Integration:
- Arctic system updates trigger sync
- Outline document changes trigger review process

## Security Configuration

### User Roles:
- **Admin**: Full access to all functions
- **Editor**: Can run syncs, view data
- **Viewer**: Can only view data

### API Rate Limiting:
- Arctic API: 100 requests/minute
- Outline API: 1000 requests/minute
- PostgreSQL: Connection pooling

## Monitoring & Alerts

### Status Monitoring:
- Sync success/failure logging
- Performance metrics
- Error tracking

### Alert Configuration:
- Email notifications for sync failures
- Slack notifications for conflicts
- Dashboard status indicators

## Deployment

### Environment Variables (Appsmith):
- POSTGRES_HOST
- POSTGRES_DB  
- POSTGRES_USER
- POSTGRES_PASSWORD
- OUTLINE_API_KEY
- ARCTIC_API_KEY
- OUTLINE_URL
- ARCTIC_URL

### Deployment Steps:
1. Deploy Appsmith applications
2. Configure data sources
3. Set up scheduled actions
4. Configure user access
5. Test all workflows