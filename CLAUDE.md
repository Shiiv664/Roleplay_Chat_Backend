# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Roleplay Chat Web App that allows users to engage in roleplay chat sessions with AI-driven characters. The application supports user profiles, characters, chat sessions, and customizable AI interactions using different models and system prompts.

## Technology Stack

- **Backend**: Python with Flask
- **Database**: SQLite
- **Frontend**: HTML, JavaScript, CSS
- **AI Interaction**: OpenRouter API (or similar)

## Architecture

The project follows a modular architecture with clear separation of concerns:

1. **Database Layer**: SQLite database with tables for characters, user profiles, AI models, system prompts, chat sessions, messages, and application settings.

2. **Backend Services**:
   - Data Access Layer (DAL) for database interactions
   - Service Layer for business logic
   - API Layer for handling HTTP requests

3. **Frontend**:
   - UI components for different pages (Home, Characters, User Profiles, System Prompts, AI Models, Settings, Chat)
   - API interaction modules for communicating with the backend
   - Core logic modules for frontend functionality

## Key Features

- User profile management
- Character browsing and management
- Chat sessions with AI-driven characters
- Support for multiple AI models
- Customizable system prompts
- Dynamic configuration of chat sessions

## Database Schema

The database includes the following tables:
- `character`: Stores character information
- `userProfile`: Stores user profile data
- `aiModel`: Tracks available AI models
- `systemPrompt`: Stores system prompts for AI interaction
- `chatSession`: Maintains chat session information
- `message`: Stores individual messages in chat sessions
- `applicationSettings`: Global app settings

## Development Guidelines

Follow these principles when modifying or adding code:
- Maintain modular structure with clear separation of concerns
- Follow Python PEP 8 style guide
- Write testable code with appropriate error handling
- Ensure security by validating input and using parameterized queries
- Maintain consistency in coding style and architecture

## Development Approach

The development of this project strictly follows a roadmap-first approach:
1. Roadmap files are created before any coding begins
2. The coding phase must follow the roadmap closely
3. Any deviations from the roadmap must be discussed and documented
4. Roadmap files serve as the source of truth for development priorities and direction