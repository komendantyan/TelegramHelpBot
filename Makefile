FUNCTION_NAME="<***>"

TELEGRAM_TOKEN="<***>"
EMERGENCY_CHAT_ID="<***>"
ALLOWED_USERNAMES="<***>"

AWS_ACCESS_KEY_ID="<***>"
AWS_SECRET_ACCESS_KEY="<***>"
AWS_BUCKET_NAME="<***>"


upload: archive
	env \
		AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
		AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
		AWS_BUCKET_NAME="${AWS_BUCKET_NAME}-source" \
		python3 upload.py
	yc serverless function version create \
		--function-name=${FUNCTION_NAME} \
		--runtime python37 \
		--entrypoint main.handler \
		--memory 128m \
		--execution-timeout 5s \
		--package-bucket-name "${FUNCTION_NAME}-source" \
		--package-object-name function.zip \
		--environment TELEGRAM_TOKEN=${TELEGRAM_TOKEN} \
		--environment EMERGENCY_CHAT_ID=${EMERGENCY_CHAT_ID} \
		--environment ALLOWED_USERNAMES=${ALLOWED_USERNAMES} \
		--environment AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
		--environment AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
		--environment AWS_BUCKET_NAME=${AWS_BUCKET_NAME}

archive: main.py Makefile requirements.txt upload.py
	rm -rf function/
	pip3 install --target function -r requirements.txt
	cp main.py Makefile requirements.txt upload.py function/
	cd function/ && zip ../function.zip -r ./*

