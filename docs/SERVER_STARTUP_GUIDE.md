# ESAB Agentic AI Welding Recommender - Server Startup Guide

## Quick Start

### 1. Start All Servers
```bash
./start_servers.sh
```

This script will:
- ✅ Kill any existing processes on ports 3000 and 8000
- ✅ Start the FastAPI backend server on port 8000
- ✅ Start the frontend server on port 3000 (React dev server or simple HTTP server)
- ✅ Show server status and URLs
- ✅ Create a stop script for easy cleanup

### 2. Stop All Servers
```bash
./stop_servers.sh
```

## Server URLs

### Backend API (Port 8000)
- **Health Check**: http://localhost:8000/api/v1/health/
- **API Documentation**: http://localhost:8000/docs
- **Enterprise Recommendations**: http://localhost:8000/api/v1/enterprise/recommendations
- **Vector Compatibility Search**: http://localhost:8000/api/v1/vector-compatibility/compatibility-search

### Frontend (Port 3000)
- **Frontend Application**: http://localhost:3000
- **Prototype Interface**: http://localhost:3000/frontend_prototype.html

## Features

### 🚀 Comprehensive Server Management
- Automatic port cleanup (kills existing processes)
- Environment validation (Python virtual env, Node.js)
- Dependency checking (pip packages, npm modules)
- Background process management with PID tracking

### 📊 Status Monitoring
- Real-time server status checking
- Health endpoint validation
- Log file creation and management
- Color-coded output for easy reading

### 🛡️ Error Handling
- Graceful error recovery
- Detailed error messages
- Environment troubleshooting
- Fallback options (simple HTTP server if React dev server fails)

### 🔧 Automatic Setup
- Creates stop script automatically
- Installs npm packages if missing
- Activates Python virtual environments
- Provides troubleshooting information

## Configuration

### Environment Variables
The system reads from `.env` file in the project root. Key settings:
- `VECTOR_CONFIDENCE_THRESHOLD=0.7` (Vector search confidence)
- `VECTOR_SEARCH_LIMIT=20` (Vector search results)
- `ENABLE_COMPATIBILITY_FALLBACK=true` (Fallback to rules-based search)

### Ports
- Backend: 8000 (FastAPI with auto-reload)
- Frontend: 3000 (React dev server or simple HTTP server)

## Log Files
- **Backend logs**: `backend.log`
- **Frontend logs**: `frontend.log`

## Troubleshooting

### Backend Issues
```bash
# Check backend logs
cat backend.log

# Test backend manually
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Issues
```bash
# Check frontend logs  
cat frontend.log

# Test frontend manually (React)
cd frontend
npm run dev

# Test frontend manually (Simple HTTP)
python3 -m http.server 3000
```

### Database Issues
- Ensure Neo4j is running on `bolt://127.0.0.1:7687`
- Check PostgreSQL connection on `localhost:5432`
- Verify database credentials in `.env` file

### Vector Search Issues
- Vector embeddings are automatically loaded during data loading
- Vector index should be online in Neo4j
- Check vector compatibility with: `curl http://localhost:8000/api/v1/vector-compatibility/compatibility-search/config`

## Development Workflow

1. **Start Development**:
   ```bash
   ./start_servers.sh
   ```

2. **Test System**:
   - Open http://localhost:3000/frontend_prototype.html
   - Try the chat interface with queries like "MIG welder for aluminum"
   - Check API docs at http://localhost:8000/docs

3. **Stop Development**:
   ```bash
   ./stop_servers.sh
   ```

## Vector Compatibility Integration

The vector compatibility search is fully integrated through the enterprise endpoint:
- **Frontend** → `/api/v1/enterprise/recommendations` 
- **Enterprise Service** → Uses 3-agent architecture
- **Smart Neo4j Agent** → Leverages vector compatibility search with 0.7 threshold
- **Results** → Users get AI-powered recommendations with vector semantic understanding

Users interact through the simple chat interface while getting sophisticated vector-powered results behind the scenes.

## Production Deployment

For production deployment:
1. Update environment variables for production databases
2. Use production WSGI server (gunicorn) instead of development server
3. Configure reverse proxy (nginx) for frontend serving
4. Set up monitoring and logging
5. Configure SSL/TLS certificates
6. Use production build for frontend (`npm run build`)

---

**🎉 The ESAB Agentic AI Welding Recommender system is ready for development and testing!**