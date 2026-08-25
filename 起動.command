#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
(
  for i in $(seq 1 50); do
    curl -s -o /dev/null "http://localhost:8501" && break
    sleep 0.2
  done
  open -a Safari "http://localhost:8501"
) &
streamlit run app.py --server.headless true
