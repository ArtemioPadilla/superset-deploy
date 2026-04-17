#!/bin/bash
# Check available Superset versions

echo "Checking available Apache Superset versions..."
echo ""

# Get latest versions from Docker Hub
echo "Recent versions on Docker Hub:"
curl -s https://hub.docker.com/v2/repositories/apache/superset/tags?page_size=10 | \
  grep -o '"name":"[^"]*"' | \
  sed 's/"name":"//;s/"//' | \
  grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | \
  sort -V -r | \
  head -10

echo ""
echo "Recommended versions:"
echo "- 5.0.0 (latest stable)"
echo "- 3.0.4 (previous stable)"
echo "- 2.1.3 (LTS)"