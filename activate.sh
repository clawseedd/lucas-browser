#!/usr/bin/env bash

if [ -f ".venv/bin/activate" ]; then
  . .venv/bin/activate
fi

export PYTHONPATH="$(pwd):$PYTHONPATH"
echo "Environment ready. Virtualenv activated if present and PYTHONPATH includes project root"
