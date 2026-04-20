CREATE TABLE IF NOT EXISTS advisory_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop TEXT NOT NULL,
    temperature REAL,
    humidity REAL,
    market_price REAL,
    alert_generated TEXT,
    action_recommended TEXT,
    priority TEXT,
    confidence REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS faqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT
);

-- Insert Mandya-specific FAQs if empty
INSERT INTO faqs (question, answer, category)
SELECT 'What is the ideal temperature for Sugarcane in Mandya?', 'Sugarcane grows best between 32°C and 38°C. In Mandya, adequate irrigation is essential during hot months.', 'Sugarcane'
WHERE NOT EXISTS (SELECT 1 FROM faqs WHERE question = 'What is the ideal temperature for Sugarcane in Mandya?');

INSERT INTO faqs (question, answer, category)
SELECT 'How to prevent blast disease in Paddy?', 'Ensure proper spacing and avoid excess nitrogen. Apply tricyclazole if symptoms appear, especially in humid conditions.', 'Paddy'
WHERE NOT EXISTS (SELECT 1 FROM faqs WHERE question = 'How to prevent blast disease in Paddy?');

INSERT INTO faqs (question, answer, category)
SELECT 'When should I harvest Ragi?', 'Ragi is ready for harvest 3-4 months after sowing, when the ears turn brown and seeds are hard.', 'Ragi'
WHERE NOT EXISTS (SELECT 1 FROM faqs WHERE question = 'When should I harvest Ragi?');

INSERT INTO faqs (question, answer, category)
SELECT 'today is hot, how will the water supply be needed for tomorrow?', 'Due to high temperatures, evaporation rates will increase. It is recommended to increase irrigation by 15-20% for the next 24 hours to maintain soil moisture, particularly for water-intensive crops like Sugarcane and Paddy.', 'Weather'
WHERE NOT EXISTS (SELECT 1 FROM faqs WHERE question = 'today is hot, how will the water supply be needed for tomorrow?');
