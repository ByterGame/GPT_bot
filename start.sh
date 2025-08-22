#!/bin/bash

java $JAVA_OPTS -jar /app/midjourney-proxy.jar &

sleep 5

python /app/bot/main.py
