#!/bin/bash

python3 /app/bot/run.py

sleep 5

java $JAVA_OPTS -jar /app/midjourney-proxy.jar &
