# Data Model Relationships

This document describes the relationships between the different models in the LLM Roleplay Chat Client.

## Entity Relationship Diagram

```
+---------------+       +---------------+       +---------------+
| UserProfile   |       | Character     |       | AIModel       |
+---------------+       +---------------+       +---------------+
| id            |       | id            |       | id            |
| label         |       | label         |       | label         |
| name          |       | name          |       | description   |
| avatar_image  |       | avatar_image  |       | created_at    |
| description   |       | description   |       +-------+-------+
| created_at    |       | created_at    |               |
| updated_at    |       | updated_at    |               |
+-------+-------+       +-------+-------+               |
        |                       |                       |
        |                       |                       |
        |                       |                       |
        |                       |                       |
+-------v-------------------------------------------------------+
|                         ChatSession                           |
+---------------------------------------------------------------+
| id            | pre_prompt         | post_prompt          |
| user_profile_id | pre_prompt_enabled | post_prompt_enabled |
| character_id  | start_time         | updated_at           |
| ai_model_id   | system_prompt_id   |                      |
+---------------+--------------------+----------------------+
                                |
                                |
                      +---------v---------+
                      |      Message      |
                      +-------------------+
                      | id                |
                      | chat_session_id   |
                      | role              |
                      | content           |
                      | timestamp         |
                      +-------------------+

                    +----------------------+
                    | ApplicationSettings  |
                    +----------------------+
                    | id (always 1)        |
                    | default_ai_model_id  |
                    | default_system_prompt_id |
                    | default_user_profile_id |
                    | default_avatar_image |
                    +----------------------+
                              |
                              |
                    +-------------------+
                    |   SystemPrompt    |
                    +-------------------+
                    | id                |
                    | label             |
                    | content           |
                    | created_at        |
                    +-------------------+
```

## Relationship Descriptions

### Independent Entities

These entities don't have required foreign keys:

1. **Character**
   - Represents a fictional character for roleplay conversations
   - Primary entity that users interact with during chat sessions

2. **UserProfile**
   - Represents a user profile for roleplay conversations
   - Users can have multiple profiles for different conversation contexts

3. **AIModel**
   - Represents an AI language model used for generating responses
   - Examples include OpenAI GPT models, Claude models, etc.

4. **SystemPrompt**
   - Represents a system prompt template used to guide the AI's behavior
   - Defines the character's personality and response style

### Dependent Entities

These entities have required foreign keys:

1. **ChatSession**
   - Central entity connecting users, characters, and messages
   - Represents an ongoing conversation between a user profile and character
   - Many-to-one relationships with Character, UserProfile, AIModel, and SystemPrompt
   - One-to-many relationship with Message

2. **Message**
   - Represents individual messages in a chat session
   - Contains message content and role (user or assistant)
   - Many-to-one relationship with ChatSession

3. **ApplicationSettings**
   - Singleton entity (only one row) for global application settings
   - Contains default values for new chat sessions
   - Many-to-one relationships with UserProfile, AIModel, and SystemPrompt

## Key Relationships

1. **ChatSession to Character**: Each chat session is associated with exactly one character.

2. **ChatSession to UserProfile**: Each chat session is associated with exactly one user profile.

3. **ChatSession to AIModel**: Each chat session uses exactly one AI model for generating responses.

4. **ChatSession to SystemPrompt**: Each chat session uses exactly one system prompt.

5. **ChatSession to Message**: Each chat session contains multiple messages (one-to-many).

6. **ApplicationSettings to defaults**: The application settings reference default entities (UserProfile, AIModel, SystemPrompt) that are used when creating new chat sessions.

## Cascade Behavior

1. **ChatSession deletion**:
   - When a Character is deleted, all associated ChatSessions are deleted (cascade)
   - When a ChatSession is deleted, all associated Messages are deleted (cascade)

2. **FK Constraints**:
   - Character to ChatSession: ON DELETE CASCADE
   - UserProfile to ChatSession: ON DELETE SET NULL
   - AIModel to ChatSession: ON DELETE SET NULL
   - SystemPrompt to ChatSession: ON DELETE SET NULL
   - ChatSession to Message: ON DELETE CASCADE

This ensures that data integrity is maintained while allowing appropriate deletion behavior.
