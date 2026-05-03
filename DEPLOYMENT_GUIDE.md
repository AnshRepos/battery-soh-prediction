# Battery Dashboard - Deployment Guide

## Table of Contents
- [Local Development Setup](#local-development-setup)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)

## Local Development Setup

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn package manager
- Git
- Text editor or IDE (VS Code recommended)

### Installation Steps

1. **Clone the Repository**
   `ash
   git clone <repository-url>
   cd battery-dashboard
   `

2. **Install Backend Dependencies**
   `ash
   cd src/services
   npm install
   `

3. **Install Frontend Dependencies**
   `ash
   cd ../..
   npm install
   `

4. **Setup Environment Variables**
   `ash
   cp .env.development .env
   `

5. **Start Development Servers**
   
   Backend (Terminal 1):
   `ash
   cd src/services
   npm start
   `
   
   Frontend (Terminal 2):
   `ash
   npm start
   `

6. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

### Development Workflow
- Frontend code changes auto-reload thanks to React's hot reload
- Backend requires manual restart on changes
- Use Chrome DevTools for debugging frontend
- Check console logs for errors

---

## Docker Deployment

### Building Docker Images

1. **Build Backend Image**
   `ash
   docker build -t battery-dashboard-backend:latest ./src/services
   `

2. **Build Frontend Image**
   `ash
   docker build -t battery-dashboard-frontend:latest ./public
   `

### Running with Docker Compose

`ash
docker-compose -f docker-compose.full.yml up -d
`

### Docker Container Ports
- Frontend: localhost:3000
- Backend API: localhost:5000
- Redis Cache: localhost:6379

### Stopping Containers
`ash
docker-compose -f docker-compose.full.yml down
`

---

## Production Deployment

### Option 1: Cloud Platforms

#### AWS EC2
1. Launch EC2 instance (Ubuntu 20.04 recommended)
2. Install Docker and Docker Compose
3. Clone repository and configure environment
4. Use docker-compose for deployment
5. Configure security groups and load balancer
6. Setup CloudWatch for monitoring

#### Heroku
1. Install Heroku CLI
2. Create new Heroku app: \heroku create battery-dashboard\
3. Push code: \git push heroku main\
4. Configure environment variables via dashboard
5. Scale dynos as needed

#### Azure Container Instances
1. Create container registry in Azure
2. Push Docker images to registry
3. Deploy using container instances or App Service
4. Configure networking and monitoring

### Option 2: On-Premises

1. **Server Setup**
   - Ubuntu Server 20.04 LTS
   - Minimum 4GB RAM, 2 CPU cores
   - 50GB storage for application and data

2. **Install Dependencies**
   `ash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose nginx certbot
   `

3. **Setup Nginx Reverse Proxy**
   `
ginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3000;
       }
       
       location /api {
           proxy_pass http://localhost:5000;
       }
   }
   `

4. **Enable SSL Certificate**
   `ash
   sudo certbot --nginx -d your-domain.com
   `

5. **Deploy Application**
   `ash
   docker-compose -f docker-compose.full.yml up -d
   `

---

## Environment Configuration

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| NODE_ENV | Environment type (development/production) | development |
| PORT | Backend server port | 5000 |
| DB_HOST | Database host | localhost |
| DB_PORT | Database port | 5432 |
| DB_USER | Database username | admin |
| DB_PASS | Database password | password |
| REDIS_URL | Redis connection URL | redis://localhost:6379 |
| API_KEY | API authentication key | - |
| LOG_LEVEL | Logging level (debug/info/warn/error) | info |
| CORS_ORIGIN | CORS allowed origin | http://localhost:3000 |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| REACT_APP_API_URL | Backend API URL | http://localhost:5000 |
| REACT_APP_ENV | Environment name | development |
| REACT_APP_VERSION | App version | 1.0.0 |

### Creating .env Files

Development (.env.development):
`
NODE_ENV=development
PORT=5000
REACT_APP_API_URL=http://localhost:5000
LOG_LEVEL=debug
`

Production (.env.production):
`
NODE_ENV=production
PORT=5000
REACT_APP_API_URL=https://api.your-domain.com
LOG_LEVEL=warn
`

---

## Monitoring and Logging

### Application Logs

Logs are stored in \logs/\ directory with rotation:
- \logs/application.log\ - General application logs
- \logs/error.log\ - Error logs
- \logs/access.log\ - Request access logs

### Log Rotation

Configure logrotate to manage log files:
`ash
/var/log/battery-dashboard/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
}
`

### Monitoring Solutions

#### Using PM2
`ash
npm install -g pm2
pm2 start ecosystem.config.js
pm2 monit
pm2 logs
`

#### Using Docker Stats
`ash
docker stats container-name
`

#### Using New Relic (Cloud APM)
1. Install New Relic agent: \
pm install newrelic\
2. Configure license key in environment
3. Restart application
4. View metrics in New Relic dashboard

#### Using Prometheus & Grafana
1. Setup Prometheus scraping backend metrics
2. Configure Grafana dashboards
3. Set up alerting rules
4. Monitor CPU, memory, request rates

### Health Checks

Backend health endpoint:
`
GET /api/health
`

Response:
`json
{
  "status": "healthy",
  "uptime": 3600,
  "timestamp": "2024-01-01T12:00:00Z"
}
`

---

## Troubleshooting

### Common Issues

#### Issue: Port Already in Use
`ash
# Find process using port 5000
sudo lsof -i :5000
# Kill process
kill -9 <PID>
`

#### Issue: Docker Container Won't Start
`ash
# Check logs
docker logs container-name
# Rebuild image
docker-compose build --no-cache
# Restart containers
docker-compose restart
`

#### Issue: Database Connection Error
- Verify DATABASE_URL is correct
- Check database is running and accessible
- Verify network connectivity
- Check firewall rules

#### Issue: CORS Errors
- Ensure CORS_ORIGIN matches frontend URL
- Check browser console for detailed error
- Verify preflight requests are being handled

#### Issue: Out of Memory
- Monitor memory usage: \docker stats\
- Reduce number of concurrent connections
- Scale up container resources
- Optimize database queries

#### Issue: API Response Slow
- Check backend logs for errors
- Monitor database query performance
- Review CPU usage on server
- Check network latency

### Performance Tuning

#### Node.js Optimization
`javascript
// Increase memory limit if needed
node --max-old-space-size=2048 server.js
`

#### Database Optimization
- Add indexes on frequently queried columns
- Archive old data periodically
- Monitor query performance

#### Caching Strategy
- Use Redis for session management
- Cache API responses with appropriate TTL
- Implement CDN for static assets

### Debugging

#### Enable Debug Logging
`ash
export DEBUG=battery-dashboard:*
npm start
`

#### Inspect Network Requests
- Use browser DevTools Network tab
- Monitor with Wireshark for deeper analysis
- Check API response times

#### Backend Debugging
`ash
node --inspect src/services/backend.js
# Access inspector at chrome://inspect
`

---

## Support and Resources

- **Documentation**: See ARCHITECTURE.md for system design
- **Contributing**: See CONTRIBUTING.md for development guidelines
- **Issues**: Report bugs via GitHub issues
- **Contact**: Your support email

