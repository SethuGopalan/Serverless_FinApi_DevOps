# Population API - Serverless Microservice

This project demonstrates deploying a **FastAPI-based Population Data Microservice** using **Nitric**, **Pulumi**, and **Dagger** with SPIRE for service identity. It is fully serverless and deployed on AWS Lambda with API Gateway.

---

## 🚀 Features

- **FastAPI** for building the microservice
- **Nitric** framework to simplify infrastructure provisioning
- **Pulumi** (via Nitric) to deploy to AWS (Lambda + API Gateway)
- **Terraform** to provision SPIRE server (mTLS + workload identity)
- **Dagger** for CI/CD pipeline automation (build + deploy)
- **Dockerized** setup, easily portable
- Secure service-to-service communication with **SPIFFE/SPIRE**

---

## 🧱 Architecture

```
+---------------------+
|  Nitric CLI (Dagger)|
+---------------------+
         |
         v
+---------------------+
| Docker Image (FastAPI)|
|  built via Dagger     |
+---------------------+
         |
         v
+-----------------------------+
| AWS Lambda + API Gateway    |
+-----------------------------+
         |
         v
+-----------------------------+
|  SPIRE Server on EC2 (Terraform) |
+-----------------------------+
```

---

## 🐳 Docker Image

The API is containerized and pushed to Docker Hub: `docker.io/7797/population-api:v1`

To build manually:
```bash
docker build -t 7797/population-api:v1 -f Dockerfile.api .
docker push 7797/population-api:v1
```

---

## 📁 Project Structure

```
.
├── api/                     # FastAPI app code
│   └── main.py
├── nitric.yaml              # Nitric project config (services, permissions)
├── nitric.dev.yaml          # Stack config (provider, region)
├── Dockerfile.api           # Docker image for FastAPI + Nitric SDK
├── Dockerfile.nitric        # Nitric CLI base image
├── dagger_spiffe.py         # Dagger pipeline: build, deploy, SPIRE setup
├── spiffesetup.tf           # Terraform config for SPIRE EC2 setup
└── README.md
```

---

## 🔐 IAM Role & Permissions

To deploy this application, an AWS IAM user/role must have permissions for:

- **Lambda & API Gateway**
  - `lambda:*`, `apigateway:*`, `iam:*` (for Nitric to create services)
- **CloudWatch Logs**
  - `logs:*`
- **S3 (if used for storage)** and **SNS (if using messaging)**:
  - `s3:*`, `sns:*`

Minimum managed policies:
```json
[
  "AWSLambda_FullAccess",
  "AmazonAPIGatewayAdministrator",
  "IAMFullAccess",
  "CloudWatchLogsFullAccess"
]
```

---

## 🧪 Run with Dagger

```bash
dagger run python dagger_spiffe.py
```

This will:

1. Destroy old SPIRE infra (Terraform)
2. Re-provision SPIRE EC2 instance
3. Build & push Docker image to Docker Hub
4. Deploy the API using Nitric (Lambda + API Gateway)
5. Optionally print the public endpoint

---

## 🔒 Security with SPIRE

- SPIRE provides **mTLS** and **workload identity** for secure service-to-service communication.
- The EC2 instance runs SPIRE server and is managed using Terraform.
- In production, this should be automated further with SPIRE agents per service.

---

## 📜 License

MIT