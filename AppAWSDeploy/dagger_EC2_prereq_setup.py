import dagger
import os
import asyncio

EC2_IP = os.environ.get("EC2_PUBLIC_IP")  # You must export this in GitHub Actions or local env
EC2_SSH_USER = os.environ.get("EC2_SSH_USER", "ubuntu")
EC2_SSH_KEY_PATH = os.environ.get("EC2_SSH_KEY_PATH", "~/.ssh/id_rsa")

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

    print(" Connecting to EC2 and preparing environment...")

    async with dagger.Connection() as client:
        ssh_dir = client.host().directory(".")

        ec2 = (
            client.container()
            .from_("ubuntu:22.04")
            .with_mounted_directory("/root/.ssh", ssh_dir)
            .with_exec(["apt", "update"])
            .with_exec(["apt", "install", "-y", "openssh-client"])
        )

        # Run setup commands via SSH
        for cmd in setup_commands():
            print(f" Running on EC2: {cmd}")
            ssh_command = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-i", EC2_SSH_KEY_PATH,
                f"{EC2_SSH_USER}@{EC2_IP}",
                cmd
            ]
            ec2 = ec2.with_exec(ssh_command)

        # Show Docker version to confirm success
        result = await ec2.with_exec([
            "ssh", "-i", EC2_SSH_KEY_PATH, f"{EC2_SSH_USER}@{EC2_IP}", "docker --version"
        ]).stdout()

        print(" EC2 Setup complete. Docker installed:")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())