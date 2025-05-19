# YouTube Search API Examples

## Basic Search

```http
GET /api/search?query=python programming
```

Searches for Python programming videos with default max results (10)

## Search with Custom Results Limit

```http
GET /api/search?query=machine learning&maxResults=5
```

Searches for machine learning videos, limiting results to 5

## Search with Special Characters

```http
GET /api/search?query=C%2B%2B tutorial
```

Searches for C++ tutorials (note URL encoding)

## Search with Multiple Words

```http
GET /api/search?query=data science for beginners
```

Searches for data science beginner content

## Search with Minimum Results

```http
GET /api/search?query=blockchain&maxResults=1
```

Searches for blockchain videos with minimum results

## Search with Maximum Results

```http
GET /api/search?query=web development&maxResults=50
```

Searches for web development videos with maximum allowed results

## Response Format

Each request returns a JSON array of video objects with the following structure:

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

## Testing Cache Behavior

Make the same request twice within the cache expiration period (1 hour) to verify Redis caching:

```http
GET /api/search?query=redis caching
```

The second request should return cached results much faster.
