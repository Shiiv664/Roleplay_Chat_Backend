-- Database schema for Roleplay Chat Web App
-- Following AI Coding Principles for clarity, modularity and scalability

-- Characters table
CREATE TABLE character (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    name TEXT NOT NULL,
    avatarImage TEXT,  -- File path or URL
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_character_label UNIQUE (label)
);

-- User profiles table
CREATE TABLE userProfile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    name TEXT NOT NULL,
    avatarImage TEXT,  -- File path or URL
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_profile_label UNIQUE (label)
);

-- AI models table
CREATE TABLE aiModel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_model_label UNIQUE (label)
);

-- System prompts table
CREATE TABLE systemPrompt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_prompt_label UNIQUE (label)
);

-- Chat sessions table
CREATE TABLE chatSession (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    startTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    character_id INTEGER NOT NULL,
    userProfile_id INTEGER NOT NULL,
    aiModel_id INTEGER NOT NULL,
    systemPrompt_id INTEGER NOT NULL,
    prePrompt TEXT,
    prePromptEnabled BOOLEAN DEFAULT 0,
    postPrompt TEXT,
    postPromptEnabled BOOLEAN DEFAULT 0,
    FOREIGN KEY (character_id) REFERENCES character(id) ON DELETE CASCADE,
    FOREIGN KEY (userProfile_id) REFERENCES userProfile(id) ON DELETE SET NULL,
    FOREIGN KEY (aiModel_id) REFERENCES aiModel(id) ON DELETE SET NULL,
    FOREIGN KEY (systemPrompt_id) REFERENCES systemPrompt(id) ON DELETE SET NULL
);

-- Messages table
CREATE TABLE message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chatSession_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chatSession_id) REFERENCES chatSession(id) ON DELETE CASCADE
);

-- Application settings (single row table)
CREATE TABLE applicationSettings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    defaultAiModel_id INTEGER,
    defaultSystemPrompt_id INTEGER,
    defaultUserProfile_id INTEGER,
    defaultAvatarImage TEXT,
    FOREIGN KEY (defaultAiModel_id) REFERENCES aiModel(id),
    FOREIGN KEY (defaultSystemPrompt_id) REFERENCES systemPrompt(id),
    FOREIGN KEY (defaultUserProfile_id) REFERENCES userProfile(id)
);

-- Indexes for performance
CREATE INDEX idx_chatSession_character ON chatSession(character_id);
CREATE INDEX idx_chatSession_userProfile ON chatSession(userProfile_id);
CREATE INDEX idx_message_chatSession ON message(chatSession_id);
CREATE INDEX idx_message_timestamp ON message(timestamp);
