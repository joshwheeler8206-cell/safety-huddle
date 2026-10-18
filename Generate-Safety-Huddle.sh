#!/bin/bash
cd ~/Desktop/work
python3 safety_huddle.py
notify-send "Safety Huddle" "PDF ready in ~/Desktop/work/" 2>/dev/null
echo "Done! PDF: ~/Desktop/work/safety-huddle-wk$(date +%V).pdf"
