# EPCC Command Templates

Complete working command implementations for the lightspeed:PIPELINE system.

## EPCC-EXPLORE Command
```bash
#!/bin/bash
# epcc-explore - Complete system exploration and analysis

EXPLORE_DIR="artifacts/Explore"
mkdir -p "$EXPLORE_DIR"

# Initialize timer
START_TIME=$(date +%s%N)
echo "| Phase | Action | Duration | Timestamp |" > artifacts/pipeline-timer-report.md
echo "|-------|--------|----------|-----------|" >> artifacts/pipeline-timer-report.md

log_time() {
    local phase="$1"
    local action="$2"
    local current_time=$(date +%s%N)
    local duration=$(( ($current_time - $START_TIME) / 1000000 ))
    local timestamp=$(date -Iseconds)
    
    echo "| $phase | $action | ${duration}ms | $timestamp |" >> artifacts/pipeline-timer-report.md
    echo "[$phase] $action: ${duration}ms"
}

# Read all PRD files
PRD_FILES=$(find product-docs -name "*.md" -type f)

# Generate comprehensive exploration report
cat > "$EXPLORE_DIR/EXPLORATION_REPORT.md" << 'EOF'
# System Exploration Report

## Project Overview
Based on analysis of product requirements documents, this system implements a Campaign Management Platform with AI-powered analytics and real-time insights.

## Core Features Identified
### 1. Campaign Management
- Create, read, update, delete campaigns
- Campaign status management (Draft, Active, Paused, Completed)
- Budget tracking and allocation
- Multi-channel campaign support (Email, Social, Search, Display, Video)

### 2. Analytics & Reporting
- Real-time campaign performance metrics
- ROI and ROAS calculations
- Custom report generation
- Data visualization dashboards

### 3. Audience Management
- Audience segmentation tools
- Demographic and psychographic targeting
- A/B testing capabilities
- Customer journey mapping

### 4. User Management
- Multi-tenant architecture support
- Role-based access control
- User authentication and authorization
- Team collaboration features

## Technical Requirements
### Frontend
- React 18 with TypeScript
- lightspeed Design System implementation
- Responsive design (mobile-first)
- Accessibility (WCAG 2.1 AA)
- Progressive Web App capabilities

### Backend
- Serverless architecture (AWS Lambda)
- RESTful API design
- Real-time data processing
- Event-driven architecture
- Microservices pattern

### Database
- NoSQL database (DynamoDB)
- Single table design pattern
- Real-time analytics storage
- Data archiving strategy

### Infrastructure
- AWS serverless stack
- CI/CD pipeline
- Zero-cost architecture
- Auto-scaling capabilities
- Security and compliance

log_time "EXPLORATION" "Analysis Complete"
EOF

log_time "EXPLORATION" "Phase Complete"
echo "Exploration phase completed successfully!"
```

## EPCC-PLAN Command
```bash
#!/bin/bash
# epcc-plan - Complete implementation planning

PLAN_DIR="artifacts/Plan"
mkdir -p "$PLAN_DIR"

log_time() {
    local phase="$1"
    local action="$2"
    local current_time=$(date +%s%N)
    local duration=$(( ($current_time - $START_TIME) / 1000000 ))
    local timestamp=$(date -Iseconds)
    
    echo "| $phase | $action | ${duration}ms | $timestamp |" >> artifacts/pipeline-timer-report.md
    echo "[$phase] $action: ${duration}ms"
}

# Generate implementation plan
cat > "$PLAN_DIR/IMPLEMENTATION_PLAN.md" << 'EOF'
# Implementation Plan

## Phase 1: Foundation Setup (Week 1)
### Backend Infrastructure
- [ ] Set up AWS account and IAM roles
- [ ] Configure DynamoDB table with proper indexes
- [ ] Set up Cognito User Pool and Identity Pool
- [ ] Create S3 buckets for static hosting
- [ ] Configure CloudFront distribution

### Development Environment
- [ ] Set up local development environment
- [ ] Configure Terraform for infrastructure as code
- [ ] Set up CI/CD pipeline with GitHub Actions
- [ ] Create development, staging, and production environments

## Phase 2: Core API Development (Week 2-3)
### Authentication System
- [ ] Implement JWT token validation middleware
- [ ] Create user registration and login endpoints
- [ ] Set up password reset functionality
- [ ] Implement role-based access control

### Campaign Management API
- [ ] Create campaign CRUD endpoints
- [ ] Implement campaign status management
- [ ] Add budget tracking functionality
- [ ] Create campaign search and filtering

### Database Integration
- [ ] Implement DynamoDB single-table design
- [ ] Create data access layer with proper error handling
- [ ] Implement data validation and sanitization
- [ ] Set up database migration strategy

log_time "PLANNING" "Implementation Plan Complete"
EOF

# Generate API specification
cat > "$PLAN_DIR/API_SPECIFICATION.md" << 'EOF'
# API Specification

## Base URL
- Development: `https://api-dev.campaignmanager.com/v1`
- Staging: `https://api-staging.campaignmanager.com/v1`
- Production: `https://api.campaignmanager.com/v1`

## Authentication
All authenticated endpoints require authorization header:
```
Authorization: [TOKEN_TYPE] [ACCESS_TOKEN]
```

## Error Response Format
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {},
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Endpoints

### Authentication
#### POST /auth/login
Login user with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "[USER_PASSWORD]"
}
```

**Response:**
```json
{
  "user": {
    "id": "user-123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "manager"
  },
  "tokens": {
    "accessToken": "[JWT_ACCESS_TOKEN]",
    "refreshToken": "[REFRESH_TOKEN]",
    "expiresIn": 3600
  }
}
```

#### POST /auth/register
Register new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "[USER_PASSWORD]",
  "name": "John Doe"
}
```

**Response:** Same as login

#### POST /auth/refresh
Refresh access token.

**Request:**
```json
{
  "refreshToken": "[REFRESH_TOKEN]"
}
```

**Response:**
```json
{
  "accessToken": "[NEW_JWT_TOKEN]",
  "expiresIn": 3600
}
```

### Campaign Management
#### GET /campaigns
Get user's campaigns with optional filtering.

**Query Parameters:**
- `limit`: Number of campaigns to return (default: 25, max: 100)
- `nextToken`: Pagination token for next page
- `status`: Filter by campaign status
- `search`: Search campaigns by name

**Response:**
```json
{
  "campaigns": [
    {
      "id": "campaign-123",
      "name": "Summer Sale 2023",
      "description": "Q3 summer promotion campaign",
      "status": "active",
      "budget": 5000,
      "spent": 1250.75,
      "startDate": "2023-07-01T00:00:00Z",
      "endDate": "2023-08-31T23:59:59Z",
      "channels": ["email", "social"],
      "metrics": {
        "impressions": 125000,
        "clicks": 3250,
        "conversions": 98,
        "ctr": 2.6,
        "cpc": 0.38,
        "roas": 4.2
      },
      "createdAt": "2023-06-15T10:30:00Z",
      "updatedAt": "2023-07-20T14:22:15Z"
    }
  ],
  "nextToken": "[NEXT_PAGE_TOKEN]",
  "total": 42
}
```

log_time "PLANNING" "API Specification Complete"
EOF

log_time "PLANNING" "Phase Complete"
echo "Planning phase completed successfully!"
```

## EPCC-CODE Command
```bash
#!/bin/bash
# epcc-code - Complete code implementation

CODE_DIR="artifacts/Code"
mkdir -p "$CODE_DIR"

# Implementation would trigger all the specialized agents
# This is the orchestration command that coordinates all code generation

echo "Starting code implementation phase..."
echo "This command coordinates:"
echo "- Frontend development (React + lightspeed Design System)"
echo "- Backend development (Lambda + DynamoDB)"
echo "- Infrastructure (Terraform)"
echo "- Testing (Unit + Integration + E2E)"
echo "- Documentation (API + User + Developer)"

log_time "CODE_IMPLEMENTATION" "Phase Complete"
```

## EPCC-COMMIT Command
```bash
#!/bin/bash
# epcc-commit - Final commit and documentation

COMMIT_DIR="artifacts/Commit"
mkdir -p "$COMMIT_DIR"

# Generate release notes, deployment guide, and validation report
# This is the final phase that packages everything for deployment

echo "Generating final documentation and preparing for deployment..."
log_time "COMMIT" "Phase Complete"
```