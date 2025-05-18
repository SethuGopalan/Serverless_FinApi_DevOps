# ServerlessFinApiDevOps

This project is a **secure, serverless financial microservice API** built using modern DevOps and cloud-native tools. It provides country-specific population data using a FastAPI backend, deployed on AWS Lambda and integrated with SPIFFE/SPIRE for identity, and Dagger for CI/CD automation.

---

## 🚀 Features

- 🌐 **FastAPI** backend serving population data
- ☁️ **Nitric** for serverless infrastructure and deployment
- 🛡️ **SPIFFE/SPIRE** for service identity and mTLS
- 🔁 **Dagger** pipelines to automate everything
- ⚙️ **Pulumi** for infrastructure provisioning
- 📈 Ready for **Datadog** observability integration
- ✅ Full automation through `dagger_spiffe.py`

---

## 📁 Project Structure

```bash
.
├── services/
│   ├── api.py                  # FastAPI service logic
│   └── Data/2021_population.csv
├── dagger_spiffe.py            # Dagger + Terraform + Nitric deploy script
├── spiffesetup.tf              # SPIRE EC2 + SG provisioning with Terraform
├── nitric.yaml                 # Nitric project configuration
├── nitric.dev.yaml             # Dev-specific stack config
├── .env.template               # Environment variable template (no secrets)
└── README.md                   # Project documentation
```

---

## 🧪 Requirements

- Python 3.10+
- AWS CLI configured with IAM access
- Docker Desktop
- Git + Dagger CLI
- Terraform CLI
- Pulumi CLI

---

## 🔐 Environment Setup

Create a `.env` file based on the provided `.env.template`:

```ini
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

> ⚠️ **Do not commit your `.env` file to GitHub.** Use `.gitignore`.

---

## 🛠️ Deployment Instructions

Run the automated pipeline with:

```bash
dagger run python dagger_spiffe.py
```

This pipeline performs:

1. **Fetches VPC/Subnet IDs** using Boto3
2. **Runs Terraform** to deploy EC2 and SPIRE
3. **Uses Nitric CLI** inside a container to deploy FastAPI to AWS Lambda via Pulumi
4. **Prints outputs** including API Gateway URL

---

## 🔄 Teardown Infrastructure

To destroy the deployed infrastructure cleanly:

```bash
dagger run python dagger_spiffe.py --destroy
```

---

## 📦 Tech Stack

| Tool       | Purpose                             |
| ---------- | ----------------------------------- |
| FastAPI    | Backend API                         |
| Nitric     | Serverless deployment framework     |
| AWS Lambda | Serverless runtime for API          |
| Pulumi     | IaC for AWS infrastructure          |
| Terraform  | EC2 + SG provisioning for SPIRE     |
| SPIFFE     | Secure service identity/mTLS        |
| Dagger     | Container-based CI/CD orchestration |
| Docker     | Local and container environments    |

---

## 🖼️ Screenshot

> Add your screenshots under `assets/` and reference them here.

```markdown
![API Demo](assets/population-api-demo.png)
```

---

## 📄 License

This project is licensed under the MIT License.
