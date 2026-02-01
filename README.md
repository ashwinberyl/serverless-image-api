# Serverless AWS Image Service API

A scalable, serverless image management API built with **AWS Lambda, API Gateway, S3, and DynamoDB**. This project demonstrates a backend architecture for handling reliable image uploads, storage, and retrieval.

---

## 🚀 Features

- **Serverless Architecture**: Completely event-driven design using AWS Lambda and API Gateway.
- **Scalable Storage**: Leverages **Amazon S3** for durable object storage and **Amazon DynamoDB** for low-latency metadata access.
- **Binary Image Support**: Correctly handles binary payloads (uploads/downloads) through API Gateway.
- **Secure Configuration**: Follows security best practices using environment variables for credentials.
- **Infrastructure as Code**: Includes Python scripts (`deploy_aws_services.py`) to programmatically deploy and configure all AWS resources.

---

## 🛠 Prerequisites

1.  **Python 3.9+**: [Download Python](https://www.python.org/downloads/)
2.  **Docker Desktop**: Required to run LocalStack. [Download Docker](https://www.docker.com/products/docker-desktop/)
3.  **curl** (Optional): For testing API endpoints from terminal.

---

## ⚙️ Setup & Installation

### 1. Clone & Prepare Environment

```bash
# Clone the repository
git clone https://github.com/ashwinberyl/serverless-image-api.git

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a file named `.env` in the root directory (or use `.env.example` as a template).

```ini
# .env content
LOCALSTACK_ENDPOINT=http://localhost:4566
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<access_id>
AWS_SECRET_ACCESS_KEY=<access_key>
S3_BUCKET_NAME=image-storage-bucket
DYNAMODB_TABLE_NAME=ImageMetadata
```

### 3. Start LocalStack Infrastructure

Start the LocalStack container (simulates AWS cloud locally).

```bash
docker-compose up -d
```

Validating startup:
```bash
docker ps
# You should see 'localstack' container running.
```

### 4. Deploy Resources (The Important Part!)

Run the setup script. This script acts as your "CloudFormation" deployer. It:
1.  Creates the S3 Bucket.
2.  Creates the DynamoDB Table.
3.  Packages your Lambda code.
4.  Creates/Updates Lambda functions.
5.  Configures API Gateway (Routes, Integrations, Binary Support).

```bash
python scripts/deploy_aws_services.py
```

**Output:**
At the end, you will see your API URL:
> Your API is ready at:
> `http://localhost:4566/restapis/<api_id>/dev/_user_request_/images`

---

## 📡 Usage Examples

Replace `<api_id>` with the ID printed by the setup script (e.g., `0huppcw5wc`).

### 1. Upload an Image
Upload a local file `sunset.jpg`.

```bash
curl -X POST "http://localhost:4566/restapis/<api_id>/dev/_user_request_/images" \
  -H "Content-Type: image/jpeg" \
  --data-binary "@sunset.jpg"
```

### 2. List Images
Get a JSON list of all uploaded images.

```bash
curl "http://localhost:4566/restapis/<api_id>/dev/_user_request_/images"
```

### 3. Download an Image (Binary)
**Important**: Use `?download=true` to get the actual binary file. Without it, you get metadata JSON.

```bash
# Replace {image_id} with an ID from the List command
curl -v "http://localhost:4566/restapis/<api_id>/dev/_user_request_/images/{image_id}?download=true" --output my_download.jpg
```

### 4. Delete an Image
Removes metadata from DynamoDB and file from S3.

```bash
curl -X DELETE "http://localhost:4566/restapis/<api_id>/dev/_user_request_/images/{image_id}"
```

---

## 📂 Project Structure

```
├── docker-compose.yml       # Defines LocalStack service + Network config
├── requirements.txt         # Python libs (boto3, requests, etc.)
├── .env                     # App secrets (Not committed to git)
├── scripts/
│   └── deploy_aws_services.py  # MAIN DEPLOY SCRIPT: Deploys all AWS resources
├── src/
│   ├── handlers/            # Lambda Functions (Upload, Get, List, Delete)
│   └── utils/               # Shared logic (AWS Clients, Response helpers)
└── tests/                   # Pytest suite
```

## 🧪 Testing

Run strict unit tests to verify logic:

```bash
pytest tests/ -v
```

---

