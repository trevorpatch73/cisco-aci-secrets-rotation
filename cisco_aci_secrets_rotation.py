import csv
import json
import requests
import random
import string
from getpass import getpass

# Prompt user for APIC URL and credentials
username = 'admin'
password = getpass("Enter local admin password: ")

# Prompt user for password requirements
length = int(input("Enter the desired length of the password: "))
special_chars = input("Enter the special characters to include (leave empty for no special characters): ")

# Generate a random password
characters = string.ascii_letters + string.digits + special_chars
new_password = ''.join(random.choice(characters) for _ in range(length))

# Define the CSV file path
csv_file = 'APIC_INVENTORY.csv'

# Initialize a list to store the device names and corresponding password change status
password_changes = []

with open(csv_file, 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        apic_ip = row['APIC_IP']

        # First API call to obtain a token
        login_url = f"https://{apic_ip}/api/aaaLogin.json"
        login_data = {
            "aaaUser": {
                "attributes": {
                    "name": f"apic#fallback\\\\{username}",
                    "pwd": password
                }
            }
        }

        response = requests.post(login_url, json=login_data, verify=False)

        if response.ok:
            token = response.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
            print(f"\nLogin successful for APIC at {apic_ip}. Obtained token.")

            # Second API call to change password
            change_password_url = f"https://{apic_ip}/api/changeSelfPassword.json?{token}"
            change_password_data = {
                "aaaChangePassword": {
                    "attributes": {
                        "userName": username,
                        "oldPassword": password,
                        "newPassword": new_password
                    }
                }
            }

            response = requests.post(change_password_url, json=change_password_data, verify=False)

            if response.ok:
                print(f"Password change successful for APIC at {apic_ip}.")

                # Test login with the new password
                test_login_url = f"https://{apic_ip}/api/aaaLogin.json"
                test_login_data = {
                    "aaaUser": {
                        "attributes": {
                            "name": f"apic#fallback\\\\{username}",
                            "pwd": new_password
                        }
                    }
                }

                response = requests.post(test_login_url, json=test_login_data, verify=False)

                if response.ok:
                    password_changes.append((row['APIC_NAME'], True))
                    print(f"Login with new password successful for APIC at {apic_ip}.")
                else:
                    password_changes.append((row['APIC_NAME'], False))
                    print(f"Login with new password failed for APIC at {apic_ip}.")
            else:
                password_changes.append((row['APIC_NAME'], False))
                print(f"Password change failed for APIC at {apic_ip}.")
        else:
            password_changes.append((row['APIC_NAME'], False))
            print(f"Login failed for APIC at {apic_ip}.")

# Print the final password applied to all APICs
print(f"\nFinal password applied to all Cisco ACI APICs: {new_password}")

# Print the password change status for each APIC
print("\nPassword change status:")
for apic_name, status in password_changes:
    print(f"{apic_name}: {'Successful' if status else 'Failed'}")