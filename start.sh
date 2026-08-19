#!/bin/bash
hermes config set model.base_url "$OPENAI_BASE_URL"
hermes config set model.api_key "$OPENAI_API_KEY"
hermes config set model.default "$HERMES_MODEL"
hermes gateway
