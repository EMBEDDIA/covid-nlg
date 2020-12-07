#!/usr/bin/env bash

PORT=${1:-8080}
LOCATION=${2:-"Finland"}
LANGUAGE=${3:-"en"}

curl -H "Content-Type: application/json" -X POST "http://localhost:${PORT}/report" -d "{
  \"location\": \"${LOCATION}\",
  \"language\": \"${LANGUAGE}\"
}"
