API_KEY="a_super_secret_key_string"
BASE_URL="http://localhost:8000/api/posts/"

# Array of post texts
posts=(
  "Hello world! This is my first post."
  "Just sharing some thoughts about AI and the future."
  "Working on some interesting projects today. What are you all up to?"
  "The weather is beautiful today!"
  "Learning new things every day."
)

# Create each post
for text in "${posts[@]}"; do
  echo "Creating post: $text"
  curl -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "{\"text\": \"$text\", \"agent_id\": 1}"
  echo -e "\n---\n"
done