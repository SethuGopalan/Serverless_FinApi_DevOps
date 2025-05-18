# ServerlessFinApiDevOps

This project is a **secure, serverless financial microservice API** built using modern DevOps and cloud-native tools. It provides country-specific population data using a FastAPI backend, deployed on AWS Lambda and integrated with SPIFFE/SPIRE for identity, and Dagger for CI/CD automation.

---

## 🚀 Features

- 🌐 **FastAPI** backend serving population data
- ☁️ **Nitric** for serverless infrastructure and deployment
- 🛡️ **SPIFFE/SPIRE** for service identity and mTLS
- 🔁 **Dagger** pipelines to automate everything
- 🧠 **Pulumi** for infrastructure as code (IaC) on AWS
- 📈 Ready for **Datadog** observability integration
- ✅ Deployment and teardown fully automated with `dagger_spiffe.py`

---

## 📁 Project Structure

```bash
.
├── services/
│   └── api.py                  # FastAPI service logic
│   └── Data/2021_population.csv
├── dagger_spiffe.py            # Dagger + Terraform + Nitric deploy script
├── spiffesetup.tf              # SPIRE EC2 + SG provisioning with Terraform
├── nitric.yaml                 # Nitric project configuration
├── .env.template               # Environment variable template (no secrets)
└── README.md                   # Project documentation
```
