-- RimTours Database Schema
-- PostgreSQL schema for tour data integration

-- Tours table (Arctic as primary source)
CREATE TABLE tours (
    id SERIAL PRIMARY KEY,
    master_name VARCHAR(255) NOT NULL,
    arctic_sync_status VARCHAR(50) DEFAULT 'pending', -- 'synced', 'pending', 'conflict'
    arctic_id VARCHAR(50),          -- Arctic identifier
    shortname VARCHAR(50),          -- Arctic shortname (authoritative)
    price DECIMAL(10,2),            -- Arctic price (authoritative)
    duration INTERVAL,              -- Arctic duration (authoritative)
    business_group VARCHAR(50),     -- Arctic business group
    variant_type VARCHAR(50),       -- Arctic variant type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Arctic data (authoritative source)
CREATE TABLE arctic_data (
    id SERIAL PRIMARY KEY,
    tour_id INTEGER REFERENCES tours(id),
    arctic_variant_data JSONB,      -- Raw Arctic data as authoritative source
    price DECIMAL(10,2),            -- From Arctic (authoritative)
    duration INTERVAL,              -- From Arctic (authoritative)
    business_group VARCHAR(50),     -- From Arctic (authoritative)
    variant_type VARCHAR(50),       -- From Arctic (authoritative)
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WordPress/Website data (supplementary)
CREATE TABLE website_data (
    id SERIAL PRIMARY KEY,
    website_id VARCHAR(50),         -- WordPress ID
    master_name VARCHAR(255),
    subtitle TEXT,                  -- From ACF fields
    region TEXT,                    -- From ACF fields
    skill_level TEXT,               -- From ACF fields
    season TEXT,                    -- From ACF fields
    short_description TEXT,         -- From ACF fields
    long_description TEXT,          -- From ACF fields
    departs_from TEXT,              -- From ACF fields
    distance TEXT,                  -- From ACF fields
    pricing_info TEXT,              -- From ACF fields (supplementary to Arctic)
    fees_info JSONB,               -- From ACF fields (supplementary)
    special_notes TEXT,            -- From ACF fields
    dates_available TEXT,          -- From ACF fields
    images_filenames TEXT,         -- From ACF fields
    reservation_link TEXT,         -- From ACF fields
    website_url TEXT,              -- Direct website URL from scraped links
    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Itinerary data (from Word docs, authoritative for route details)
CREATE TABLE itinerary_data (
    id SERIAL PRIMARY KEY,
    tour_id INTEGER REFERENCES tours(id),
    day_number INTEGER,
    route_description TEXT,
    miles DECIMAL(6,2),
    elevation_gain TEXT,
    camp_lodging TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sync requests (for manual review when Arctic doesn't support updates)
CREATE TABLE sync_requests (
    id SERIAL PRIMARY KEY,
    arctic_shortname VARCHAR(50),
    changes JSONB,
    status VARCHAR(50) DEFAULT 'pending_review', -- 'pending_review', 'approved', 'rejected'
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    approved_at TIMESTAMP,
    approved_by VARCHAR(100)
);

-- Indexes for performance
CREATE INDEX idx_tours_arctic_id ON tours(arctic_id);
CREATE INDEX idx_tours_shortname ON tours(shortname);
CREATE INDEX idx_website_data_website_id ON website_data(website_id);
CREATE INDEX idx_arctic_data_tour_id ON arctic_data(tour_id);
CREATE INDEX idx_itinerary_tour_id ON itinerary_data(tour_id);