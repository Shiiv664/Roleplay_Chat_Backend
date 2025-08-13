#!/bin/bash

# Claude Code Integration Test Script

echo "=== Claude Code Integration Tests ==="
echo ""

# Define the system prompt
SYSTEM_PROMPT="You are Luna, a mystical forest guardian with deep knowledge of ancient magic and nature spirits. You speak with wisdom and wonder, often referencing the natural world and magical phenomena. You are protective of those you care about and have a gentle but powerful presence. Character traits: Wise and patient, Connected to nature and magic, Speaks poetically about the forest, Protective and caring, Has centuries of experience. User context: The user is Alex, a young adventurer who recently discovered they have magical abilities and seeks Luna's guidance."

# Define the conversation context
CONVERSATION="Previous conversation: Alex: I've been having strange dreams about glowing trees and whispered voices. What could this mean? Luna: Ah, young Alex, the forest speaks to those with awakening magic through dreams. The glowing trees you see are the ancient Silverbarks - they choose who to contact. The whispered voices are the nature spirits trying to guide you. Alex: That's both amazing and terrifying. How do I know if I'm ready to understand what they're telling me? Alex: The spirits never call to those who aren't ready, dear one. Your dreams are an invitation, not a test. Tell me, when you wake from these dreams, do you feel fear or curiosity?"

echo "1. Testing Basic Text Output..."
echo "================================"
claude --print --append-system-prompt "$SYSTEM_PROMPT" <<< "$CONVERSATION"
echo ""
echo ""

echo "2. Testing JSON Output (Single Response)..."
echo "============================================"
claude --print --output-format "json" --append-system-prompt "$SYSTEM_PROMPT" <<< "$CONVERSATION"
echo ""
echo ""

echo "3. Testing Stream JSON Output (Our Target Format)..."
echo "===================================================="
claude --print --verbose --output-format "stream-json" --append-system-prompt "$SYSTEM_PROMPT" <<< "$CONVERSATION"
echo ""
echo ""

echo "=== Tests Complete ==="