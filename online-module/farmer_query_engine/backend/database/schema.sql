-- SQLite schema for Farmer Query Engine

CREATE TABLE IF NOT EXISTS diseases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    treatment TEXT,
    fertilizer TEXT,
    prevention TEXT
);

CREATE TABLE IF NOT EXISTS yojnas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    crop TEXT,
    state TEXT,
    disease TEXT,            -- optional: scheme is disease-specific (NULL = applies to all)
    description TEXT,
    link TEXT                -- official scheme URL
);

CREATE TABLE IF NOT EXISTS centers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    address TEXT
);

CREATE TABLE IF NOT EXISTS crop_health_tips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop TEXT NOT NULL,
    tips TEXT
);
