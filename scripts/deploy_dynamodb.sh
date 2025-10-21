# ---- config you can tweak ----
PROFILE=SBPOC11_HACKATHON
REGION=us-east-1
SEED_FILE=seed-flight-offer.json
SEED_KEY=dynamodb/seed-flight-offer.json
STACK=dynamo-seeded-table
TABLE_NAME=request_2_table_test
TEMPLATE=cloudformation.yaml

# Make a unique bucket name (date + random suffix)
BUCKET="yajun-seed-$(date +%Y%m%d)-$RANDOM"

echo "Using bucket: $BUCKET"

# 0) Confirm which account this profile uses (so bucket is created in the right place)
aws sts get-caller-identity --profile "$PROFILE" --region "$REGION"

# 1) Create the bucket (special case: us-east-1 needs no LocationConstraint)
aws s3api create-bucket \
  --bucket "$BUCKET" \
  --region "$REGION" \
  --profile "$PROFILE"

# 2) (Optional) enable default encryption at rest
aws s3api put-bucket-encryption \
  --bucket "$BUCKET" \
  --region "$REGION" \
  --profile "$PROFILE" \
  --server-side-encryption-configuration '{
    "Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]
  }'

# 3) Upload your seed JSON (must be a TOP-LEVEL ARRAY)
aws s3 cp "$SEED_FILE" "s3://$BUCKET/$SEED_KEY" \
  --region "$REGION" \
  --profile "$PROFILE" \
  --content-type application/json

# 4) Deploy the stack pointing at THIS new bucket
aws cloudformation deploy \
  --template-file "$TEMPLATE" \
  --stack-name "$STACK" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      TableName="$TABLE_NAME" \
      SeedDataBucket="$BUCKET" \
      SeedDataKey="$SEED_KEY" \
  --region "$REGION" \
  --profile "$PROFILE"

