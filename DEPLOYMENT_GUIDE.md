# Production Deployment Guide

This guide explains how to use the production deployment system for the roleplay web application on ARM ChromeOS VM.

## Quick Start

### 1. Setup Environment
```bash
# Setup development environment
./scripts/setup-environment.sh development

# Setup production environment
./scripts/setup-environment.sh production

# Generate encryption keys for both environments
./scripts/generate-encryption-key.sh development
./scripts/generate-encryption-key.sh production
```

### 2. Development Mode
```bash
# Start development servers (Flask + Vite)
./scripts/dev-start.sh

# Check status
./scripts/status.sh dev

# View logs
./scripts/logs.sh dev --follow

# Stop development servers
./scripts/dev-stop.sh
```

### 3. Production Deployment
```bash
# Full deployment (build frontend + start production server)
./scripts/deploy.sh

# Or deploy from git repository
./scripts/deploy-from-git.sh main --backup

# Check production status
./scripts/status.sh prod

# View production logs
./scripts/logs.sh prod --follow
```

## Architecture Overview

### Development Mode (Two Servers)
- **Backend**: Flask development server on `http://127.0.0.1:5000`
- **Frontend**: Vite development server on `http://localhost:5173`
- **Benefits**: Hot-reload, fast development cycle

### Production Mode (Single Server)
- **Single Server**: Flask serves both API and React static files on `http://localhost:8080`
- **Benefits**: Simplified deployment, no CORS issues, single process to manage

## Environment Configuration

### Environment Files
- `.env.development` - Development settings
- `.env.production` - Production settings
- `.env.example` - Template file (safe to commit)

### Key Variables
```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false
FLASK_HOST=0.0.0.0
FLASK_PORT=8080

# Database
DATABASE_URL=sqlite:///app_prod.db

# Security (auto-generated)
SECRET_KEY=auto-generated-secure-key
ENCRYPTION_KEY=auto-generated-encryption-key
```

## Script Reference

### Environment Management
```bash
./scripts/setup-environment.sh [development|production]  # Setup/validate environment
./scripts/generate-encryption-key.sh [development|production]  # Generate security keys
```

### Development Scripts
```bash
./scripts/dev-start.sh     # Start development servers
./scripts/dev-stop.sh      # Stop development servers
```

### Production Scripts
```bash
./scripts/build-frontend.sh   # Build React app for production
./scripts/prod-start.sh       # Start production server
./scripts/prod-stop.sh        # Stop production server
./scripts/deploy.sh           # Full deployment (build + start)
```

### Management Scripts
```bash
./scripts/status.sh [dev|prod]        # Check service status
./scripts/logs.sh [service] [--follow] # View logs
./scripts/restart.sh [dev|prod]       # Restart services
```

### Git Deployment
```bash
./scripts/deploy-from-git.sh [branch] [--backup] [--force]
```

## Process Management (ARM ChromeOS VM Compatible)

### Background Processes
- Uses `nohup` for ARM ChromeOS VM compatibility
- PID files stored in `pids/` directory
- Automatic cleanup on stop
- Health checks and port conflict detection

### Service Status
```bash
# Check all services
./scripts/status.sh

# Check specific service
./scripts/status.sh dev
./scripts/status.sh prod
```

### Log Management
```bash
# View all logs
./scripts/logs.sh

# Follow specific service logs
./scripts/logs.sh prod --follow

# View more lines
./scripts/logs.sh --lines 100
```

## Deployment Workflows

### Local Development Deployment
1. Make changes to code
2. Test in development mode: `./scripts/dev-start.sh`
3. Deploy to production: `./scripts/deploy.sh`

### Git-based Deployment
1. Push changes to repository
2. Deploy from git: `./scripts/deploy-from-git.sh main --backup`
3. Monitor logs: `./scripts/logs.sh prod --follow`

### Rollback
If git deployment creates a rollback script:
```bash
./rollback_to_abc12345.sh
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
lsof -Pi :8080 -sTCP:LISTEN

# Kill the process
sudo lsof -Ti :8080 | xargs sudo kill -9
```

#### Service Won't Start
```bash
# Check logs
./scripts/logs.sh prod

# Check environment
./scripts/setup-environment.sh production

# Force restart
./scripts/restart.sh prod --force
```

#### Frontend Not Loading
```bash
# Rebuild frontend
./scripts/build-frontend.sh

# Check if files exist
ls -la frontend_build/

# Redeploy
./scripts/deploy.sh
```

### Log Locations
- Development Backend: `backend_dev.log`
- Development Frontend: `../Roleplay_Chat_Frontend/frontend_dev.log`
- Production: `production.log`
- Archived logs: `*.log.YYYYMMDD_HHMMSS`

### Health Checks
```bash
# Manual health check
curl http://localhost:8080/

# API check
curl http://localhost:8080/api/v1/

# Frontend check
curl http://localhost:8080/ | grep "<!DOCTYPE html>"
```

## Security Considerations

### Auto-Generated Keys
- Encryption keys are automatically generated when missing
- Keys are stored in environment files
- Different keys for development vs production

### Database Security
- Production uses separate database file
- Environment-specific database URLs
- Automatic migrations support

### Network Security
- Development: Localhost binding (127.0.0.1)
- Production: External binding (0.0.0.0) for network access
- Configurable ports to avoid conflicts

## ARM ChromeOS VM Optimizations

### Background Process Management
- Uses `nohup` with output redirection
- PID file tracking for reliable process management
- Graceful shutdown with fallback force-kill

### Memory Efficiency
- Single server architecture in production
- Log rotation to prevent disk space issues
- Cleanup of stale processes and ports

### Development Workflow
- Fast ARM64 esbuild support (documented in CLAUDE.md)
- Efficient development server management
- Quick restart capabilities

## Monitoring and Maintenance

### Regular Checks
```bash
# Daily status check
./scripts/status.sh

# Weekly log cleanup
find . -name "*.log.*" -mtime +7 -delete

# Monthly backup
./scripts/deploy-from-git.sh main --backup
```

### Performance Monitoring
- Service status includes memory usage
- Response time checks in health monitoring
- Process uptime tracking

### Updates and Maintenance
```bash
# Update from git with backup
./scripts/deploy-from-git.sh main --backup

# Restart services gracefully
./scripts/restart.sh graceful

# Check system health
./scripts/status.sh
```

## Advanced Usage

### Custom Environment Variables
Add to your `.env.production` file:
```bash
# Custom configurations
CUSTOM_SETTING=value
EXTERNAL_SERVICE_URL=https://example.com
```

### Database Migrations
Automatic migration support with Alembic:
```bash
# Migrations run automatically during git deployments
# Manual migration
alembic upgrade head
```

### Backup and Recovery
```bash
# Create backup before deployment
./scripts/deploy-from-git.sh main --backup

# Backup location
ls ../backups/
```

This deployment system provides a robust, script-based approach to managing your roleplay web application in both development and production environments, optimized for ARM ChromeOS VM constraints.