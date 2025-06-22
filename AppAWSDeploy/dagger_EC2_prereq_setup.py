import dagger
import os
import asyncio
import base64
# from pathlib import Path # Not strictly needed anymore for local file ops

# Directly get environment variables
EC2_IP = os.environ.get("EC2_PUBLIC_IP")
EC2_SSH_USER = os.environ.get("EC2_SSH_USER")
EC2_SSH_KEY_B64 = os.environ.get("EC2_SSH_KEY") # This is now the correct variable name

# No need for EC2_SSH_PRIVATE_KEY, EC2_SSH_KEY_PATH, or the prepare_ssh_key() function
# as we'll handle the key directly within Dagger.

# Commands to install tools on the EC2 instance
def setup_commands(ssh_user): # Pass user for the usermod command
    return [
        "sudo apt update",
        "sudo apt install -y python3-pip curl unzip git",
        # Nitric install often adds to PATH in .bashrc/.profile, which SSH non-login shells don't source.
        # So, we'll try to find common bin directories or just rely on user's setup after this.
        # For a robust setup, you might use 'sudo install' to put binaries in /usr/local/bin.
        "curl -fsSL https://nitric.io/install | bash",
        "curl -fsSL https://get.pulumi.com | sh",
        "curl -L https://dl.dagger.io/dagger/install.sh | sh",
        "sudo mv dagger /usr/local/bin/dagger",
        "pip3 install dagger-io boto3", # This installs on EC2 for the *runner agent*, not within the Dagger container.
        "sudo apt update && sudo apt install -y docker.io", # More robust Docker install needed here.
        "sudo systemctl start docker",
        "sudo systemctl enable docker", # Ensure Docker starts on boot
        f"sudo usermod -aG docker {ssh_user}",
        "echo 'User added to docker group. Re-login or restart GitHub Actions runner agent on EC2.'"
    ]

async def main():
    if not EC2_IP:
        print("Error: EC2_PUBLIC_IP is not set.")
        return
    if not EC2_SSH_USER:
        print("Error: EC2_SSH_USER is not set.")
        return
    if not EC2_SSH_KEY_B64:
        raise EnvironmentError("EC2_SSH_KEY environment variable is not set. Please ensure it's provided as a GitHub Secret.")

    print(" Preparing SSH key for Dagger container...")
    
    # Decode the base64 SSH key
    try:
        ec2_ssh_key_contents = base64.b64decode(EC2_SSH_KEY_B64).decode('utf-8')
    except Exception as e:
        print(f"Error decoding EC2_SSH_KEY: {e}")
        return

    print(" Connecting to EC2 and preparing environment...")

    async with dagger.Connection() as client:
        # Create a container with SSH client installed.
        # We will directly add the private key as a file within this container.
        # Alpine/git has ssh-client and is lightweight.
        ssh_container = (
            client.container()
            .from_("alpine/git:latest") # Use a small image with git and ssh client
            .with_exec(["apk", "add", "--no-cache", "openssh-client"]) # Ensure ssh client is installed
            # Create .ssh directory and add the key with correct permissions
            .with_exec(["mkdir", "-p", "/root/.ssh"])
            # Add the key directly as a new file in the container
            .with_new_file("/root/.ssh/id_rsa", contents=ec2_ssh_key_contents, permissions=0o400)
            # Add known_hosts to avoid host key checking prompts (only if trusted)
            # Alternatively, leave StrictHostKeyChecking=no in ssh command
            # .with_exec(["ssh-keyscan", "-H", EC2_IP, ">>", "/root/.ssh/known_hosts"]) # This requires shell in container, use withShell
            # Or better, just ensure StrictHostKeyChecking=no is in your ssh command as you have it.
        )

        # Iterate through setup commands and execute them via SSH
        for cmd in setup_commands(EC2_SSH_USER): # Pass user here
            print(f"  Running on EC2: {cmd}")
            # The SSH command needs to be executed within the ssh_container
            ssh_exec_args = [
                "ssh", "-o", "StrictHostKeyChecking=no", # Still useful for initial connection
                "-i", "/root/.ssh/id_rsa", # This path is now relative to the Dagger container!
                f"{EC2_SSH_USER}@{EC2_IP}",
                cmd
            ]
            ssh_container = ssh_container.with_exec(ssh_exec_args) # Chain the commands

        # After all setup commands, execute a final verification command
        print("\nVerifying Docker installation on EC2...")
        verify_command = [
            "ssh", "-i", "/root/.ssh/id_rsa",
            f"{EC2_SSH_USER}@{EC2_IP}",
            "docker --version" # Or 'docker info' for more detail
        ]

        try:
            result = await ssh_container.with_exec(verify_command).stdout()
            print(" EC2 Setup complete. Docker installed and verified:")
            print(result)
        except dagger.ExecError as e:
            print(f" Error during EC2 setup or verification: {e}")
            print(f"Stderr: {e.stderr}")
            print(f"Stdout: {e.stdout}")
            raise # Re-raise to fail the GitHub Actions step
        except Exception as e:
            print(f" An unexpected error occurred: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())