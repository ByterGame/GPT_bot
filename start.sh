java -jar /app/midjourney-proxy.jar --server.port=8080 &

sleep 5

python /app/bot/run.py
