import dagger
import os
import asyncio
import base64
from pathlib import Path

EC2_IP = os.environ.get("EC2_PUBLIC_IP")
EC2_SSH_KEY = os.environ.get("EC2_SSH_PRIVATE_KEY")
EC2_SSH_KEY_B64 = os.environ.get("EC2_SSH_KEY")  # This is the base64-encoded key

# Path where the decoded key will be stored
EC2_SSH_KEY_PATH = str(Path.home() / ".ssh" / "id_rsa")

# Decode the base64 SSH key and save it locally
def prepare_ssh_key():
    if not EC2_SSH_KEY_B64:
        raise EnvironmentError("EC2_SSH_KEY environment variable is not set.")
    
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    key_path = ssh_dir / "id_rsa"
    with open(key_path, "w") as key_file:
        key_file.write(base64.b64decode(EC2_SSH_KEY_B64).decode("utf-8"))
    os.chmod(key_path, 0o600)
    return str(key_path)

# Commands to install tools on the EC2 instance
def setup_commands():
    return [
        "sudo apt update",
        "sudo apt install -y python3-pip curl unzip git",
        "curl -fsSL https://nitric.io/install | bash",
        "curl -fsSL https://get.pulumi.com | sh",
        "curl -L https://dl.dagger.io/dagger/install.sh | sh",
        "sudo mv dagger /usr/local/bin/dagger",
        "pip3 install dagger-io boto3",
        "sudo apt install -y docker.io",
        "sudo systemctl start docker",
        f"sudo usermod -aG docker {EC2_SSH_USER}"
    ]

async def main():
    if not EC2_IP:
        print(" EC2_PUBLIC_IP is not set.")
        return

    print("🔑 Preparing SSH key...")
    prepare_ssh_key()

    print("🔗 Connecting to EC2 and preparing environment...")

    async with dagger.Connection() as client:
        ssh_dir = client.host().directory(".")  # Host bind mount

        ec2 = (
            client.container()
            .from_("ubuntu:22.04")
            .with_mounted_directory("/root/.ssh", ssh_dir)
            .with_exec(["apt", "update"])
            .with_exec(["apt", "install", "-y", "openssh-client"])
        )

        for cmd in setup_commands():
            print(f"  Running on EC2: {cmd}")
            ssh_command = [
                "ssh", "-o", "StrictHostKeyChecking=no",
                "-i", EC2_SSH_KEY_PATH,
                f"{EC2_SSH_USER}@{EC2_IP}",
                cmd
            ]
            ec2 = ec2.with_exec(ssh_command)

        result = await ec2.with_exec([
            "ssh", "-i", EC2_SSH_KEY_PATH,
            f"{EC2_SSH_USER}@{EC2_IP}",
            "docker --version"
        ]).stdout()

        print(" EC2 Setup complete. Docker installed:")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
