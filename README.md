# retention-peaks

A Python-based YouTube search bot that utilizes the YouTube Data API v3 for searching videos and managing search history. The bot includes MongoDB for persistent storage and Redis for caching search results.

## Features

- Search YouTube videos with caching support
- Fetch detailed video information
- Store and retrieve search history
- RESTful API endpoints
- MongoDB integration for persistent storage
- Redis caching for improved performance

## Prerequisites

- Python 3.x
- MongoDB (running locally or accessible instance)
- Redis (running locally or accessible instance)
- YouTube Data API v3 key

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and update the configuration:
   ```bash
   cp .env.example .env
   ```
5. Update the `.env` file with your YouTube API key and database configurations

## Database Setupdat

### MongoDB Setup

1. Install MongoDB from the [official website](https://www.mongodb.com/try/download/community)
2. Start MongoDB service:
   - Linux/macOS: `sudo systemctl start mongod`
   - Windows: MongoDB runs as a service automatically
3. Verify MongoDB is running on default port 27017
4. Update `MONGODB_URI` in `.env` file if using a different configuration

### Redis Setup

1. Install Redis:
   - Linux/macOS: Use package manager or [download](https://redis.io/download)
   - Windows: Use [Windows Subsystem for Linux](https://redis.io/docs/getting-started/installation/install-redis-on-windows/)
2. Start Redis server:
   - Linux/macOS: `redis-server`
   - Windows WSL: `sudo service redis-server start`
3. Verify Redis is running on default port 6379
4. Update Redis configuration in `.env` if using different settings

## Configuration

Update the following environment variables in the `.env` file:

- `YOUTUBE_API_KEY`: Your YouTube Data API v3 key
- `MONGODB_URI`: MongoDB connection string (default: mongodb://localhost:27017/youtube_bot)
- `REDIS_HOST`: Redis host (default: localhost)
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_PASSWORD`: Redis password (if required)
- `PORT`: Application port (default: 8000)
- `NODE_ENV`: Environment (development/production)

## Development

Start the development server:

```bash
uvicorn src.main:app --reload
```

## Production

Start the production server:

```bash
uvicorn src.main:app
```

## API Documentation

### Search Videos

```http
GET /api/search?query=<search_term>&maxResults=<number>
```

#### Parameters

- `query` (required): Search term
- `maxResults` (optional): Maximum number of results (default: 10)

#### Response Format

```json
[
  {
    "id": "video_id",
    "title": "Video Title",
    "description": "Video Description",
    "thumbnail_url": "https://example.com/thumbnail.jpg",
    "published_at": "2024-01-01T00:00:00Z",
    "channel_title": "Channel Name"
  }
]
```

### Get Video Details

```http
GET /api/video/{id}
```

#### Parameters

- `id`: YouTube video ID

### Get Search History

```http
GET /api/history
```

Returns the last 10 searches

## Troubleshooting

### Common Issues

1. **MongoDB Connection Issues**

   - Verify MongoDB is running: `mongo` or `mongosh`
   - Check MongoDB URI in `.env`
   - Ensure MongoDB port is not blocked by firewall

2. **Redis Connection Issues**

   - Verify Redis is running: `redis-cli ping`
   - Check Redis configuration in `.env`
   - Ensure Redis port is accessible

3. **YouTube API Issues**
   - Verify API key is valid
   - Check daily quota limits
   - Ensure API is enabled in Google Cloud Console

## Dependencies

- FastAPI (>=0.104.0): Web framework
- Uvicorn (>=0.24.0): ASGI server
- Motor (>=3.3.1): Async MongoDB driver
- Redis (>=5.0.1): Redis client
- Google API Python Client (>=2.106.0): YouTube API client
- Additional dependencies listed in `requirements.txt`

## License

ISC
