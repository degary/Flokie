# Deployment Guide

This guide covers deployment procedures for the Flask API Template across different environments.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Deployment Scripts](#deployment-scripts)
- [Environment-Specific Deployment](#environment-specific-deployment)
- [Security Considerations](#security-considerations)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Overview

The Flask API Template supports deployment to multiple environments:

- **Development** (`dev`): Local development environment
- **Testing** (`test`): Automated testing environment
- **Acceptance** (`acc`): User acceptance testing environment
- **Staging** (`staging`): Pre-production staging environment
- **Production** (`prod`): Live production environment

Each environment has its own configuration, security settings, and deployment procedures.

## Prerequisites

### System Requirements

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Python** 3.11+ (for local development)
- **OpenSSL** (for secrets generation)
- **Git** (for version control)

### Access Requirements

- Docker registry access (for production deployments)
- Database server access (PostgreSQL for production)
- Redis server access (for caching and sessions)
- SSL certificates (for HTTPS in production)

## Environment Configuration

### Environment Files

Each environment uses a specific configuration file:

```bash
.env.dev      # Development configuration
.env.test     # Testing configuration
.env.acc      # Acceptance configuration
.env.prod     # Production configuration
```

### Configuration Setup

1. **Copy environment template:**
   ```bash
   cp .env.example .env.dev
   ```

2. **Use setup script:**
   ```bash
   ./scripts/setup_env.sh dev
   ```

3. **Manual configuration:**
   Edit the environment file with appropriate values for your environment.

### Required Environment Variables

#### All Environments
- `FLASK_CONFIG`: Environment name (dev, test, acc, prod)
- `SECRET_KEY`: Application secret key (32+ characters)
- `JWT_SECRET_KEY`: JWT signing key (32+ characters)
- `DATABASE_URL`: Database connection string

#### Production Environments (acc, prod)
- `POSTGRES_PASSWORD`: PostgreSQL password
- `REDIS_PASSWORD`: Redis password
- `CORS_ORIGINS`: Allowed CORS origins
- `SENTRY_DSN`: Error tracking DSN (optional)
- `NEW_RELIC_LICENSE_KEY`: APM license key (optional)

## Deployment Scripts

### Main Deployment Script

The main deployment script handles all environment deployments:

```bash
./scripts/deploy.sh [ENVIRONMENT] [ACTION] [OPTIONS]
```

#### Examples

```bash
# Deploy to development
./scripts/deploy.sh dev up

# Deploy to production with rebuild
./scripts/deploy.sh prod up --build

# Show production logs
./scripts/deploy.sh prod logs

# Stop acceptance environment
./scripts/deploy.sh acc down

# Scale production app to 3 replicas
./scripts/deploy.sh prod up --scale 3
```

### Secrets Management

Generate and manage secrets securely:

```bash
# Generate secrets for production
./scripts/manage_secrets.sh generate prod

# Rotate secrets
./scripts/manage_secrets.sh rotate prod

# Export secrets for deployment
./scripts/manage_secrets.sh export prod -o prod.env
```

### Configuration Validation

Validate environment configuration:

```bash
# Validate production configuration
python scripts/validate_config.py prod

# Validate all configurations
for env in dev test acc prod; do
    python scripts/validate_config.py $env
done
```

## Environment-Specific Deployment

### Development Environment

**Purpose**: Local development and testing

**Deployment**:
```bash
# Setup development environment
./scripts/setup_env.sh dev --database

# Start development services
./scripts/deploy.sh dev up

# Access application
curl http://localhost:5001/api/health
```

**Features**:
- SQLite database
- Debug mode enabled
- Hot reloading
- Detailed error messages

### Testing Environment

**Purpose**: Automated testing and CI/CD

**Deployment**:
```bash
# Run tests in Docker
./scripts/deploy.sh test up

# Run specific test command
docker-compose -f docker-compose.test.yml run --rm app pytest tests/
```

**Features**:
- In-memory database
- Test-specific configuration
- Coverage reporting
- Isolated test environment

### Acceptance Environment

**Purpose**: User acceptance testing and stakeholder review

**Deployment**:
```bash
# Generate secrets
./scripts/manage_secrets.sh generate acc

# Setup environment
./scripts/setup_env.sh acc --secrets --database

# Deploy to acceptance
./scripts/deploy.sh acc up --build

# Validate deployment
./scripts/deploy.sh acc status
```

**Features**:
- PostgreSQL database
- Redis caching
- Production-like configuration
- Monitoring enabled

### Production Environment

**Purpose**: Live production system

**Pre-deployment Checklist**:
- [ ] Secrets generated and secured
- [ ] SSL certificates configured
- [ ] Database backups verified
- [ ] Monitoring systems ready
- [ ] Rollback plan prepared

**Deployment**:
```bash
# Generate production secrets
./scripts/manage_secrets.sh generate prod

# Validate configuration
python scripts/validate_config.py prod

# Create backup (if existing deployment)
./scripts/deploy.sh prod backup

# Deploy to production
./scripts/deploy.sh prod up --build

# Verify deployment
./scripts/deploy.sh prod status
curl https://your-domain.com/api/health
```

**Features**:
- PostgreSQL with connection pooling
- Redis with persistence
- Nginx reverse proxy
- SSL/TLS encryption
- Security headers
- Resource limits
- Health checks
- Logging and monitoring

## Security Considerations

### Secrets Management

1. **Never commit secrets to version control**
2. **Use strong, randomly generated secrets**
3. **Rotate secrets regularly**
4. **Store secrets securely in production**

### Container Security

1. **Run containers as non-root user**
2. **Use read-only filesystems where possible**
3. **Apply security options (no-new-privileges)**
4. **Limit container capabilities**
5. **Use specific image tags, not 'latest'**

### Network Security

1. **Use HTTPS in production**
2. **Configure proper CORS origins**
3. **Implement rate limiting**
4. **Use secure session cookies**
5. **Enable security headers**

### Database Security

1. **Use strong database passwords**
2. **Enable SSL connections**
3. **Restrict database access**
4. **Regular security updates**
5. **Database encryption at rest**

## Monitoring and Maintenance

### Health Checks

All environments include comprehensive health checks:

```bash
# Check application health
curl http://localhost:5001/api/health

# Check Docker container health
docker ps --filter "health=healthy"

# Run comprehensive health check
docker exec <container> /app/docker/healthcheck.sh
```

### Logging

Centralized logging configuration:

- **Development**: Console output with debug level
- **Production**: Structured JSON logs with warning level
- **Log rotation**: Automatic with size and time limits
- **Log aggregation**: Sentry integration for error tracking

### Monitoring

Production monitoring includes:

- **Application Performance Monitoring (APM)**: New Relic integration
- **Error Tracking**: Sentry integration
- **Health Checks**: Docker health checks and custom endpoints
- **Resource Monitoring**: Docker stats and system metrics

### Backup Procedures

#### Database Backups

```bash
# Create database backup
./scripts/deploy.sh prod backup

# Manual database backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U flask_user flask_prod > backup.sql
```

#### Application Data Backups

```bash
# Backup application data
docker-compose -f docker-compose.prod.yml exec app tar -czf - /app/instance > app_data.tar.gz
```

### Update Procedures

1. **Test updates in lower environments first**
2. **Create backups before updates**
3. **Use rolling updates for zero-downtime**
4. **Verify functionality after updates**
5. **Have rollback plan ready**

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check container logs
./scripts/deploy.sh prod logs

# Check container status
docker ps -a

# Inspect container configuration
docker inspect <container_name>
```

#### Database Connection Issues

```bash
# Check database container
docker-compose -f docker-compose.prod.yml exec db pg_isready

# Test database connection
docker-compose -f docker-compose.prod.yml exec app python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.engine.execute('SELECT 1')
print('Database connection successful')
"
```

#### Performance Issues

```bash
# Check resource usage
docker stats

# Check application metrics
curl http://localhost:5001/api/health

# Review logs for errors
./scripts/deploy.sh prod logs | grep ERROR
```

### Debug Mode

For troubleshooting, you can enable debug mode temporarily:

```bash
# Enable debug logging
docker-compose -f docker-compose.prod.yml exec app \
  python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Your debug code here
"
```

### Recovery Procedures

#### Application Recovery

```bash
# Restart application
./scripts/deploy.sh prod restart

# Rollback to previous version
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --scale app=2
```

#### Database Recovery

```bash
# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T db \
  psql -U flask_user flask_prod < backup.sql
```

### Getting Help

1. **Check logs first**: `./scripts/deploy.sh [env] logs`
2. **Validate configuration**: `python scripts/validate_config.py [env]`
3. **Check system resources**: `docker stats`
4. **Review documentation**: This guide and code comments
5. **Check monitoring systems**: Sentry, New Relic dashboards

## Best Practices

1. **Always test in lower environments first**
2. **Use infrastructure as code**
3. **Implement proper monitoring**
4. **Maintain comprehensive backups**
5. **Document all procedures**
6. **Regular security updates**
7. **Capacity planning and scaling**
8. **Disaster recovery planning**

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Nginx Documentation](https://nginx.org/en/docs/)
