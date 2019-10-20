
FUNCTION_NAME="<fill>"

TELEGRAM_TOKEN="<fill>"
EMERGENCY_CHAT_ID="<fill>"
ALLOWED_USERNAMES="<fill>"


run:
	env \
		TELEGRAM_TOKEN=${TELEGRAM_TOKEN} \
		EMERGENCY_CHAT_ID=${EMERGENCY_CHAT_ID} \
		ALLOWED_USERNAMES=${ALLOWED_USERNAMES} \
		USE_TOR=1 \
		python3 main.py

archive:
	zip function.zip main.py

upload: archive
	yc serverless function version create \
		--function-name=${FUNCTION_NAME} \
		--runtime python37 \
		--entrypoint main.handler \
		--memory 128m \
		--execution-timeout 5s \
		--source-path ./function.zip \
		--environment TELEGRAM_TOKEN=${TELEGRAM_TOKEN} \
		--environment EMERGENCY_CHAT_ID=${EMERGENCY_CHAT_ID} \
		--environment ALLOWED_USERNAMES=${ALLOWED_USERNAMES}
