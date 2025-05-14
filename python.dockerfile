FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# COPY . /app/

COPY . .


# ENTRYPOINT ["python", "-u", "api.py"]
# # 
ENTRYPOINT ["nitric", "start"]
# CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "16002", "--reload"]

# FROM python:3.12-slim



# WORKDIR /app

# COPY . /app/ 




# # Install curl for downloading nitric
# RUN apt-get update && apt-get install -y curl && apt-get clean

# # Install Nitric CLI
# RUN curl -fsSL https://nitric.io/install.sh | bash

# ENV PATH="/root/.nitric/bin:$PATH"

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .
# ENTRYPOINT ["python", "-u", "services/api.py"]

# # ENTRYPOINT ["nitric"]
# # CMD ["start"]



