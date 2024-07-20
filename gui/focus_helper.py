import sys
import os

hosts_path = r"C:\Windows\System32\drivers\etc\hosts" if sys.platform == "win32" else "/etc/hosts"
blocked_websites_file = "blocked_websites.txt"

def read_blocked_websites():
    if os.path.exists(blocked_websites_file):
        with open(blocked_websites_file, "r") as file:
            return file.read().splitlines()
    return []

def save_blocked_websites(websites):
    with open(blocked_websites_file, "w") as file:
        file.write("\n".join(websites))

def block_website(website):
    try:
        with open(hosts_path, "a") as file:
            file.write(f"127.0.0.1 {website}\n")
        print(f"Blocked {website}")
    except PermissionError:
        print(f"Permission denied when trying to block {website}")

def unblock_website(website):
    try:
        with open(hosts_path, "r") as file:
            lines = file.readlines()
        
        with open(hosts_path, "w") as file:
            for line in lines:
                if website not in line:
                    file.write(line)
        print(f"Unblocked {website}")
    except PermissionError:
        print(f"Permission denied when trying to unblock {website}")

def unblock_all_websites():
    try:
        with open(hosts_path, "r") as file:
            lines = file.readlines()

        with open(hosts_path, "w") as file:
            for line in lines:
                if "127.0.0.1" not in line:
                    file.write(line)
        print("Unblocked all websites")
    except PermissionError:
        print("Permission denied when trying to unblock all websites")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: focus_helper.py <block|unblock|unblock_all> [website]")
        sys.exit(1)

    action = sys.argv[1]
    blocked_websites = read_blocked_websites()
    
    if action == "block" and len(sys.argv) == 3:
        website = sys.argv[2]
        block_website(website)
        if website not in blocked_websites:
            blocked_websites.append(website)
        save_blocked_websites(blocked_websites)
    elif action == "unblock" and len(sys.argv) == 3:
        website = sys.argv[2]
        unblock_website(website)
        if website in blocked_websites:
            blocked_websites.remove(website)
        save_blocked_websites(blocked_websites)
    elif action == "unblock_all":
        unblock_all_websites()
        save_blocked_websites([])
    else:
        print("Invalid arguments")
        sys.exit(1)
