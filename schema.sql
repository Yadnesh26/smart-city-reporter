CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    area TEXT NOT NULL,
    latitude TEXT,
    longitude TEXT,
    image_filename TEXT,
    status TEXT DEFAULT 'Pending',
    resolved_image_filename TEXT,
    upvote_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS upvotes (
    user_id TEXT,
    issue_id INTEGER,
    PRIMARY KEY (user_id, issue_id)
);
