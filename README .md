# Serverless FastAPI Microservice with SPIFFE/SPIRE and Nitric Deployment

This project deploys a **FastAPI-based serverless microservice** to AWS using [Nitric](https://nitric.io/), and provisions a secure SPIFFE/SPIRE server on EC2. It uses a **Dagger pipeline** to automate infrastructure deployment and service provisioning.

---

## 🔧 Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [Nitric Framework](https://nitric.io/)
- [SPIFFE/SPIRE](https://spiffe.io/)
- [Dagger](https://dagger.io/)
- [Terraform](https://terraform.io/)
- AWS (Lambda, EC2, IAM, VPC, Subnet, Security Group)

---

## 📁 Project Structure

```bash
ServerlessFinApiDevOps/
├── api.py                        # FastAPI microservice
├── nitric.yaml                   # Default nitric project configuration
├── nitric.dev.yaml               # Deployment-specific stack file
├── spiffesetup.tf                # Terraform for provisioning SPIRE on EC2
├── dagger_spiffe.py              # Dagger pipeline for deployment
├── Dockerfile.nitric             # Custom Dockerfile with Nitric CLI (optional)
├── services/                     # FastAPI service directory
├── .env                          # AWS credentials (not committed)
├── README.md                     # You are here
```

---

## 🚀 Deployment Instructions

### 1. ✅ Prerequisites

- AWS CLI configured (`aws configure`)
- IAM user with permissions for:
  - `ec2:*`, `iam:*`, `lambda:*`, `cloudformation:*`, `ssm:*`
- Docker Desktop installed and running
- Python 3.11+
- [Dagger CLI](https://docs.dagger.io/install)
- Nitric CLI (optional for local testing)

---

### 2. 🌐 Setup Environment Variables

Create a `.env` file in the root directory:

```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

---

### 3. 🧠 Run the Dagger Pipeline

This command deploys:
1. The FastAPI service to AWS via Nitric
2. A SPIRE server EC2 instance via Terraform

```bash
dagger run python dagger_spiffe.py
```

---

### 4. ✅ Verify Deployment

- Check AWS Lambda and API Gateway for the deployed FastAPI.
- Check EC2 console for SPIRE server instance.
- Use `Postman` or `curl` to access your API.

---

## 📌 Notes

- If `nitric-dev.yaml` is not detected, rename or verify the path inside the container.
- `dagger_spiffe.py` manages VPC, subnet, and SPIRE provisioning with auto-fetch.
- All tools run in containers—no local installations are required.

---

## 🧹 Cleanup

```bash
dagger run python dagger_spiffe.py --destroy
```

> (Ensure you implement a destroy flag in your script to trigger `terraform destroy`)

---

## 📄 License

MIT © 2025 Sethu Gopalan
