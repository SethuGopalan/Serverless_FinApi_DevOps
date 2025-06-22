import dagger
import os
import asyncio
import base64

EC2_IP = os.environ.get("EC2_PUBLIC_IP")
EC2_SSH_USER = os.environ.get("EC2_SSH_USER")
EC2_SSH_KEY_B64 = os.environ.get("EC2_SSH_KEY")

def setup_commands(ssh_user):
    commands = [
        "sudo apt update",
        "sudo apt install -y python3-pip curl unzip git",
        "curl -fsSL https://nitric.io/install | bash",
        "curl -fsSL https://get.pulumi.com | sh",
        "pip3 install dagger-io boto3",
        
        "mkdir -p /tmp/dagger_install",
        "curl -L https://dl.dagger.io/dagger/releases/latest/dagger-linux-amd64 > /tmp/dagger_install/dagger",
        "chmod +x /tmp/dagger_install/dagger",
        "sudo mv /tmp/dagger_install/dagger /usr/local/bin/dagger",
        "rmdir /tmp/dagger_install",
        
        # --- FIX FOR DOCKER GPG ERROR (Attempt 2: Modern approach) ---
        "sudo apt update",
        "sudo apt install -y ca-certificates curl gnupg", # gnupg is still useful for general crypto
        "sudo install -m 0755 -d /etc/apt/keyrings", # Ensure directory exists
        
        # Download the GPG key directly and place it using tee.
        # This avoids the explicit gpg --dearmor command which can cause TTY issues.
        # The 'signed-by' option in sources.list can handle the armored key directly.
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.gpg > /dev/null",
        
        "sudo chmod a+r /etc/apt/keyrings/docker.gpg", # Set correct permissions
        
        # Now, the sources.list entry referencing the key:
        "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
        
        "sudo apt update",
        "sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
        "sudo systemctl start docker",
        "sudo systemctl enable docker",
        f"sudo usermod -aG docker {ssh_user}",
        "echo 'User added to docker group. Re-login or restart GitHub Actions runner agent on EC2.'"
    ]
    return commands

async def main():
    if not EC2_IP:
        print("Error: EC2_PUBLIC_IP is not set.")
        return
    if not EC2_SSH_USER:
        print("Error: EC2_SSH_USER is not set.")
        return
    if not EC2_SSH_KEY_B64:
        raise EnvironmentError("EC2_SSH_KEY environment variable is not set. Please ensure it's provided as a GitHub Secret.")

    print("🔑 Preparing SSH key for Dagger container...")
    
    try:
        ec2_ssh_key_contents = base64.b64decode(EC2_SSH_KEY_B64).decode('utf-8')
    except Exception as e:
        print(f"Error decoding EC2_SSH_KEY: {e}")
        return

    print("🔗 Connecting to EC2 and preparing environment...")

    async with dagger.Connection() as client:
        ssh_container = (
            client.container()
            .from_("ubuntu:22.04")
            .with_exec(["apt", "update"])
            .with_exec(["apt", "install", "-y", "openssh-client"])
            .with_exec(["mkdir", "-p", "/root/.ssh"])
            .with_new_file("/root/.ssh/id_rsa", contents=ec2_ssh_key_contents, permissions=0o400)
        )

        for cmd in setup_commands(EC2_SSH_USER):
            print(f"  Running on EC2: {cmd}")
            ssh_exec_args = [
                "ssh", "-o", "StrictHostKeyChecking=no",
                "-i", "/root/.ssh/id_rsa",
                f"{EC2_SSH_USER}@{EC2_IP}",
                cmd
            ]
            ssh_container = ssh_container.with_exec(ssh_exec_args)

        print("\nVerifying Docker installation on EC2...")
        verify_command = [
            "ssh", "-i", "/root/.ssh/id_rsa",
            f"{EC2_SSH_USER}@{EC2_IP}",
            "docker --version"
        ]

        try:
            result = await ssh_container.with_exec(verify_command).stdout()
            print("EC2 Setup complete. Docker installed and verified:")
            print(result)
        except dagger.ExecError as e:
            print(f"Error during EC2 setup or verification: {e}")
            print(f"Stderr: {e.stderr}")
            print(f"Stdout: {e.stdout}")
            raise
        except Exception as e:
            print(f" An unexpected error occurred: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())