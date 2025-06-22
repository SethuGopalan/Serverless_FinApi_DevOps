import dagger
import os
import asyncio
import base64

EC2_IP = os.environ.get("EC2_PUBLIC_IP")
EC2_SSH_USER = os.environ.get("EC2_SSH_USER")
EC2_SSH_KEY_B64 = os.environ.get("EC2_SSH_KEY") # This is now the correct variable name

# Commands to install tools on the EC2 instance
def setup_commands(ssh_user):
    commands = [
        "sudo apt update",
        "sudo apt install -y python3-pip curl unzip git",
        # Nitric CLI - often added to ~/.nitric/bin. We'll rely on it being added to PATH
        # for a user, or source .profile for actual runner.
        "curl -fsSL https://nitric.io/install | bash",
        # Pulumi CLI - often added to ~/.pulumi/bin
        "curl -fsSL https://get.pulumi.com | sh",
        # Python dependencies for the runner (if it runs locally)
        "pip3 install dagger-io boto3", # This installs for the EC2 user
        
        # --- FIX FOR DAGGER INSTALLATION ---
        # 1. Create a temporary directory or use /tmp
        # 2. Download the dagger binary directly to a known location
        # 3. Move it from that known location to /usr/local/bin
        "mkdir -p /tmp/dagger_install",
        "curl -L https://dl.dagger.io/dagger/releases/latest/dagger-linux-amd64 > /tmp/dagger_install/dagger", # Download directly
        "chmod +x /tmp/dagger_install/dagger", # Make it executable
        "sudo mv /tmp/dagger_install/dagger /usr/local/bin/dagger", # Move from known path
        "rmdir /tmp/dagger_install", # Clean up temp directory
        # --- END FIX ---

        # Docker installation - more robust version
        "sudo apt update",
        "sudo apt install -y ca-certificates curl gnupg",
        "sudo install -m 0755 -d /etc/apt/keyrings",
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
        "sudo chmod a+r /etc/apt/keyrings/docker.gpg",
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
    
    # Decode the base64 SSH key
    try:
        ec2_ssh_key_contents = base64.b64decode(EC2_SSH_KEY_B64).decode('utf-8')
    except Exception as e:
        print(f"Error decoding EC2_SSH_KEY: {e}")
        return

    print("🔗 Connecting to EC2 and preparing environment...")

    async with dagger.Connection() as client:
        ssh_container = (
            client.container()
            .from_("ubuntu:22.04") # Using Ubuntu as it's common for runners
            .with_exec(["apt", "update"])
            .with_exec(["apt", "install", "-y", "openssh-client"])
            .with_exec(["mkdir", "-p", "/root/.ssh"])
            .with_new_file("/root/.ssh/id_rsa", contents=ec2_ssh_key_contents, permissions=0o400)
        )

        for cmd in setup_commands(EC2_SSH_USER):
            print(f"  Running on EC2: {cmd}")
            ssh_exec_args = [
                "ssh", "-o", "StrictHostKeyChecking=no", # Still useful for initial connection
                "-i", "/root/.ssh/id_rsa", # This path is now relative to the Dagger container!
                f"{EC2_SSH_USER}@{EC2_IP}",
                cmd
            ]
            ssh_container = ssh_container.with_exec(ssh_exec_args)

        # After all setup commands, execute a final verification command
        print("\nVerifying Docker installation on EC2...")
        verify_command = [
            "ssh", "-i", "/root/.ssh/id_rsa",
            f"{EC2_SSH_USER}@{EC2_IP}",
            "docker --version"
        ]

        try:
            result = await ssh_container.with_exec(verify_command).stdout()
            print(" EC2 Setup complete. Docker installed and verified:")
            print(result)
        except dagger.ExecError as e:
            print(f" Error during EC2 setup or verification: {e}")
            print(f"Stderr: {e.stderr}")
            print(f"Stdout: {e.stdout}")
            raise
        except Exception as e:
            print(f" An unexpected error occurred: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())