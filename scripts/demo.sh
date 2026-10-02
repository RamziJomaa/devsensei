#!/bin/bash

# Ensure jq is installed
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required to parse JSON responses. Please install it (e.g., sudo apt install jq or brew install jq)."
    exit 1
fi

REPO_URL=${1:-"https://github.com/langchain-ai/langgraph"}
echo "🚀 Submitting repository for DevSensei analysis: $REPO_URL"

# Submit Analysis
SUBMIT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/analyse \
    -H "Content-Type: application/json" \
    -d "{\"repo_url\": \"$REPO_URL\"}")

ANALYSIS_ID=$(echo $SUBMIT_RESPONSE | jq -r '.analysis_id')

if [ "$ANALYSIS_ID" == "null" ] || [ -z "$ANALYSIS_ID" ]; then
    echo "❌ Failed to submit analysis. Backend response:"
    echo $SUBMIT_RESPONSE
    exit 1
fi

echo "✅ Analysis started successfully. ID: $ANALYSIS_ID"
echo "⏳ Polling for status..."

# Poll Status
while true; do
    STATUS_RESPONSE=$(curl -s http://localhost:8000/api/v1/analysis/$ANALYSIS_ID/status)
    STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
    
    if [ "$STATUS" == "done" ]; then
        echo -e "\n🎉 Analysis complete!"
        break
    elif [ "$STATUS" == "failed" ]; then
        echo -e "\n❌ Analysis failed during execution."
        exit 1
    fi
    
    echo -n "🤖 "
    sleep 3
done

# Fetch Report
echo -e "\n📄 Fetching final report..."
REPORT_RESPONSE=$(curl -s http://localhost:8000/api/v1/report/$ANALYSIS_ID)

echo -e "\n=========================================="
echo $REPORT_RESPONSE | jq -r '.markdown_content'
echo "=========================================="

echo -e "\n📊 LLM-as-a-Judge Eval Scores:"
echo "Faithfulness: $(echo $REPORT_RESPONSE | jq -r '.faithfulness_score')"
echo "Actionability: $(echo $REPORT_RESPONSE | jq -r '.avg_actionability')"
echo "Relevance: $(echo $REPORT_RESPONSE | jq -r '.avg_finding_relevance')"
