import requests
import json
import os
import argparse
from dotenv import load_dotenv
from jsonschema import validate, ValidationError

# Load environment variables from .env file
load_dotenv()

# Spoolman instance URL (loaded from .env)
spoolman_url = os.getenv("SPOOLMAN_URL")

# Function to send POST request to create a filament
def create_filament(filament):
    url = f"{spoolman_url}/api/v1/filament"
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, data=json.dumps(filament))
    return response

# Function to send POST request to create a vendor
def create_vendor(vendor_name):
    url = f"{spoolman_url}/api/v1/vendor"
    headers = {
        'Content-Type': 'application/json'
    }
    vendor = {"name": vendor_name}
    response = requests.post(url, headers=headers, data=json.dumps(vendor))
    return response

# Function to get a vendor by name
def get_vendor_by_name(vendor_name):
    url = f"{spoolman_url}/api/v1/vendor"
    response = requests.get(url, params={"name": vendor_name})
    if response.status_code == 200 and response.json():
        return response.json()[0]  # Assuming the API returns a list of matching vendors
    return None

# Function to get a filament by name
def get_filament_by_name(filament_name):
    url = f"{spoolman_url}/api/v1/filament"
    response = requests.get(url, params={"name": filament_name})
    if response.status_code == 200 and response.json():
        return response.json()[0]  # Assuming the API returns a list of matching filaments
    return None

# Function to get all vendors
def get_vendors():
    url = f"{spoolman_url}/api/v1/vendor"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Function to get all filaments
def get_filaments():
    url = f"{spoolman_url}/api/v1/filament"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Function to delete a vendor by ID
def delete_vendor(vendor_id):
    url = f"{spoolman_url}/api/v1/vendor/{vendor_id}"
    response = requests.delete(url)
    return response

# Function to delete a filament by ID
def delete_filament(filament_id):
    url = f"{spoolman_url}/api/v1/filament/{filament_id}"
    response = requests.delete(url)
    return response

# Function to merge colors safely
def merge_colors(filament, new_color):
    if not any(color['name'] == new_color['name'] for color in filament["colors"]):
        filament["colors"].append(new_color)

# Function to create vendors and filaments
def create_data():
    # URL to fetch the JSON data
    data_url = "https://donkie.github.io/SpoolmanDB/filaments.json"

    # Fetch the data from the provided URL
    response = requests.get(data_url)
    response.raise_for_status()  # Check if the request was successful
    data = response.json()

    # Extract the filaments from the data
    filaments = data

    # Create all vendors first
    vendor_creation_results = {"created": 0, "exists": 0}
    for item in filaments:
        manufacturer_name = item["manufacturer"]

        # Check if the vendor exists
        existing_vendor = get_vendor_by_name(manufacturer_name)
        if existing_vendor:
            vendor_id = existing_vendor["id"]
            vendor_creation_results["exists"] += 1
        else:
            response = create_vendor(manufacturer_name)
            if response.status_code == 200:
                vendor_data = response.json()
                vendor_id = vendor_data["id"]
                vendor_creation_results["created"] += 1
            else:
                print(f"Failed to create vendor: {manufacturer_name}. Status code: {response.status_code}, Error: {response.text}")

    # Output vendor creation summary
    print(f"Vendor creation summary: {vendor_creation_results['created']} created, {vendor_creation_results['exists']} already existed")

    # Refresh the list of existing vendors
    vendors = get_vendors()
    existing_vendors = {vendor['name']: vendor for vendor in vendors}

    # Process and format the filaments
    filament_creation_results = {"created": 0, "merged": 0}
    for item in filaments:
        manufacturer_name = item["manufacturer"]
        vendor_id = existing_vendors[manufacturer_name]["id"]

        filament_name = item["name"]
        existing_filament = get_filament_by_name(filament_name)
        if existing_filament:
            filament_creation_results["merged"] += 1
            # Merge colors for the existing filament
            for color in item.get("colors", []):
                merge_colors(existing_filament, {
                    "name": color["name"],
                    "hex": color["color_hex"]
                })
            continue

        # Ensure diameters are correctly formatted and not missing
        diameters = item.get("diameter")
        if not diameters:
            continue

        try:
            diameters = [float(diameters)] if isinstance(diameters, (int, float)) else [float(d) for d in diameters]
        except ValueError:
            continue

        # Ensure spool_weight is greater than 0
        spool_weight = item.get("spool_weight", 1)  # Default to 1 if not provided or invalid
        if spool_weight <= 0:
            spool_weight = 1

        filament = {
            "name": filament_name,
            "material": item.get("material"),
            "density": item.get("density", 1.0),
            "weight": item.get("weight", 0),
            "spool_weight": spool_weight,
            "diameter": item.get("diameter", 1.75),
            "settings_extruder_temp": item.get("extruder_temp", 200),
            "settings_bed_temp": item.get("bed_temp", 60),
            "color_hex": item.get("color_hex"),
            "external_id": item.get("id"),
            "vendor_id": vendor_id  # Use the vendor_id from the created vendor
        }

        # Send the POST request to create the filament
        response = create_filament(filament)
        if response.status_code == 200:
            filament_creation_results["created"] += 1

    # Output filament creation summary
    print(f"Filament creation summary: {filament_creation_results['created']} created, {filament_creation_results['merged']} merged")

    print("All filaments processed.")

# Function to delete all vendors and filaments
def delete_all_data():
    # Fetch and delete all filaments
    filaments = get_filaments()
    for filament in filaments:
        filament_id = filament['id']
        response = delete_filament(filament_id)
        if response.status_code == 204:
            print(f"Successfully deleted filament: {filament['name']} (ID: {filament_id})")
        else:
            print(f"Failed to delete filament: {filament['name']} (ID: {filament_id}). Status code: {response.status_code}, Error: {response.text}")

    # Fetch and delete all vendors
    vendors = get_vendors()
    for vendor in vendors:
        vendor_id = vendor['id']
        response = delete_vendor(vendor_id)
        if response.status_code == 204:
            print(f"Successfully deleted vendor: {vendor['name']} (ID: {vendor_id})")
        else:
            print(f"Failed to delete vendor: {vendor['name']} (ID: {vendor_id}). Status code: {response.status_code}, Error: {response.text}")

    print("All vendors and filaments deleted.")

# Main function to parse CLI arguments and execute the appropriate function
def main():
    parser = argparse.ArgumentParser(description="Manage Spoolman data.")
    parser.add_argument("action", choices=["create", "delete"], help="Action to perform: 'create' to add data, 'delete' to remove data")
    args = parser.parse_args()

    if args.action == "create":
        create_data()
    elif args.action == "delete":
        delete_all_data()

if __name__ == "__main__":
    main()
