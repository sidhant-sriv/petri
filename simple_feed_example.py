#!/usr/bin/env python3
import requests


def fetch_feed(base_url="http://localhost:8000", api_key="a_super_secret_key_string", limit=5):
    """
    Simple function to fetch posts from the World service feed endpoint
    
    Args:
        base_url: URL of the World service (default: http://localhost:8000)
        api_key: API key for authentication (default: a_super_secret_key_string)
        limit: Number of posts to fetch (default: 5)
    
    Returns:
        List of posts or empty list if error
    """
    url = f"{base_url}/api/feed/"
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    params = {'limit': limit}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises an exception for bad status codes
        
        posts = response.json()
        return posts
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching feed: {e}")
        return []


def print_feed_simple(posts):
    """Print feed posts in a simple format"""
    if not posts:
        print("No posts found!")
        return
    
    print(f"Found {len(posts)} posts:")
    print("-" * 40)
    
    for post in posts:
        author_name = post['author']['name']
        post_text = post['text']
        comment_count = len(post.get('comments', []))
        
        print(f"📝 {author_name}: {post_text}")
        if comment_count > 0:
            print(f"   💬 {comment_count} comment(s)")
        print()


if __name__ == "__main__":
    # Fetch and display the feed
    print("🌍 Fetching World Feed...")
    feed_posts = fetch_feed(limit=10)
    print_feed_simple(feed_posts)
