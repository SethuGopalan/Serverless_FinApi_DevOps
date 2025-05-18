# 🌍 Serverless Population API with Nitric, SPIFFE, Dagger, and Pulumi

This project demonstrates a modern DevOps pipeline for deploying a **FastAPI-based microservice** that serves population data using **Nitric**, **Terraform**, **Pulumi**, **SPIFFE/SPIRE**, and **Dagger**. It showcases secure service-to-service communication, automated deployment, and AWS infrastructure provisioning.

---

## 🚀 Tech Stack Overview

| Tool             | Purpose                                            |
| ---------------- | -------------------------------------------------- |
| **FastAPI**      | Web framework for building the API                 |
| **Nitric**       | Infrastructure-as-code + deployment for serverless |
| **Pulumi**       | Cloud infrastructure provisioning in code          |
| **Terraform**    | SPIRE server/agent provisioning on AWS EC2         |
| **Dagger**       | CI/CD pipelines for deployment automation          |
| **SPIFFE/SPIRE** | Secure workload identity and mTLS                  |
| **AWS Lambda**   | Serverless backend compute for the API             |
| **AWS EC2**      | Host for SPIRE server                              |

---

## 📦 API Features

- Endpoint: `GET /population`
- Query Parameters:
  - `country` – Name of the country (e.g., `India`)
  - `year` – `2020` or `2021`
- Returns the population value for the given year and country from a local CSV file stored in the project.

---

## 🛠️ Setup Instructions

### 1. Clone and Install Requirements

```bash
git clone https://github.com/SethuGopalan/ServerlessFinApiDevOps.git
cd ServerlessFinApiDevOps
pip install -r requirements.txt
```

### 2. AWS IAM Role Requirements

You must create or use an AWS IAM user or role with the following permissions:

#### ✅ Required Managed Policies:

- `AmazonEC2FullAccess`
- `AmazonVPCFullAccess`
- `AmazonSSMFullAccess`
- `IAMFullAccess`
- `AWSLambda_FullAccess`
- `AmazonAPIGatewayAdministrator`
- `AmazonS3FullAccess`

#### ✅ Important Inline Permissions:

These are required to support SPIRE provisioning and Nitric deployments:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateSecurityGroup",
        "ec2:DescribeSecurityGroups",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupEgress",
        "ec2:RunInstances",
        "ec2:CreateTags",
        "ec2:DescribeInstances",
        "iam:PassRole",
        "ssm:GetParameter",
        "ssm:PutParameter"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## ⚙️ Project Structure

```plaintext
.
├── services/
│   └── api.py                # FastAPI code with Nitric SDK
│   └── Data/2021_population.csv
├── dagger_spiffe.py          # Python pipeline to deploy API + SPIRE
├── spiffesetup.tf            # Terraform config for SPIRE provisioning
├── nitric.yaml               # Nitric config file
├── Dockerfile                # Optional container build
├── .env                      # AWS credentials (excluded from repo)
└── README.md                 # This file
```

---

## ▶️ Running the Dagger Pipeline

Run the full deployment:

```bash
dagger run python dagger_spiffe.py
```

This will:

1. Pull your default VPC and subnet.
2. Deploy the FastAPI-based Nitric API to AWS using Pulumi.
3. Provision an EC2 instance with SPIRE using Terraform.
4. Secure the deployment with SPIFFE-based mTLS.

---

## 🌐 Example API Usage

### ✅ Successful Request:

```bash
curl "https://your-api-gateway-url/population?country=India&year=2021"
```

```json
{
  "country": "India",
  "year": "2021",
  "population": 1393409038
}
```

---

## 🧪 Testing & Monitoring

- **CloudWatch**: Check logs for API and SPIRE instance.
- **Postman**: Easily test the endpoint with query parameters.
- **Datadog (optional)**: Can be integrated for monitoring Lambda/API Gateway metrics.

---

## 🔐 SPIRE Setup Notes

- A dedicated EC2 instance is provisioned with SPIRE server running on port `8081`.
- Future extension can include a SPIRE agent and automatic SPIFFE ID issuance for services.

---

## 📄 License

This project is under the MIT License.

---

## 🙌 Author

**Sethu Gopalan**  
🌐 GitHub: [@SethuGopalan](https://github.com/SethuGopalan)

---

## 📢 Feedback

Contributions, ideas, and improvements are welcome! Feel free to open an issue or PR.
