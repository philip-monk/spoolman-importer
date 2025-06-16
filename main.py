import requests
import json
import os
import argparse
from dotenv import load_dotenv

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
def create_vendor(vendor):
    url = f"{spoolman_url}/api/v1/vendor"
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, data=json.dumps(vendor))
    return response

# Function to send POST request to create a material
def create_material(material):
    url = f"{spoolman_url}/api/v1/material"
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, data=json.dumps(material))
    return response

# Function to get all vendors
def get_vendors():
    url = f"{spoolman_url}/api/v1/vendor"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Function to get all materials
def get_materials():
    url = f"{spoolman_url}/api/v1/material"
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

# Function to delete a material by ID
def delete_material(material_id):
    url = f"{spoolman_url}/api/v1/material/{material_id}"
    response = requests.delete(url)
    return response

# Function to delete a filament by ID
def delete_filament(filament_id):
    url = f"{spoolman_url}/api/v1/filament/{filament_id}"
    response = requests.delete(url)
    return response

# Function to create vendors and filaments
def create_data():
    # URL to fetch the JSON data
    filaments_data_url = "https://donkie.github.io/SpoolmanDB/filaments.json"
    materials_data_url = "https://donkie.github.io/SpoolmanDB/materials.json"

    # Fetch the filament data from the provided URL
    print("Fetching filament data from SpoolmanDB...")
    try:
        response = requests.get(filaments_data_url)
        response.raise_for_status()  # Check if the request was successful
        filaments_data = response.json()
        print(f"Found {len(filaments_data)} filament definitions.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching filament data from source URL: {e}")
        return

    # --- Material Processing ---
    print("Processing materials...")
    # Fetch the material data from the provided URL
    print("Fetching material data from SpoolmanDB...")
    try:
        response = requests.get(materials_data_url)
        response.raise_for_status()
        materials_data = response.json()
        print(f"Found {len(materials_data)} material definitions.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching material data from source URL: {e}")
        return

    # Get all existing materials from Spoolman
    try:
        existing_materials_list = get_materials()
        existing_material_names = {material['name'] for material in existing_materials_list}
        print(f"Found {len(existing_material_names)} existing materials in Spoolman.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching materials from Spoolman: {e}")
        return

    # Determine which materials need to be created
    materials_to_create = [
        material for material in materials_data
        if material.get("name") and material["name"] not in existing_material_names
    ]

    # Create all missing materials
    material_creation_results = {"created": 0, "failed": 0}
    if materials_to_create:
        print(f"Creating {len(materials_to_create)} new materials...")
        for material_data in materials_to_create:
            response = create_material(material_data)
            if 200 <= response.status_code < 300:
                material_creation_results["created"] += 1
            else:
                material_creation_results["failed"] += 1
                print(f"Failed to create material: {material_data.get('name')}. Status code: {response.status_code}, Error: {response.text}")

    print(f"Material creation summary: {material_creation_results['created']} created, {len(existing_material_names)} already existed, {material_creation_results['failed']} failed.")

    # Refresh the list of materials to get IDs for all
    try:
        all_materials_list = get_materials()
        material_map = {material['name']: material['id'] for material in all_materials_list}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching materials from Spoolman after creation: {e}")
        return

    # --- Vendor Processing ---
    print("Processing vendors...")
    # Get all existing vendors from Spoolman
    try:
        existing_vendors_list = get_vendors()
        existing_vendor_names = {vendor['name'] for vendor in existing_vendors_list}
        print(f"Found {len(existing_vendor_names)} existing vendors in Spoolman.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching vendors from Spoolman: {e}")
        return

    # Determine which vendors need to be created by inferring from filaments.json
    all_vendor_names = {item["manufacturer"] for item in filaments_data if item.get("manufacturer")}
    vendors_to_create_names = all_vendor_names - existing_vendor_names

    # Create all missing vendors
    vendor_creation_results = {"created": 0, "failed": 0}
    if vendors_to_create_names:
        print(f"Creating {len(vendors_to_create_names)} new vendors...")
        for vendor_name in vendors_to_create_names:
            vendor_payload = {"name": vendor_name}
            response = create_vendor(vendor_payload)
            if 200 <= response.status_code < 300:
                vendor_creation_results["created"] += 1
            else:
                vendor_creation_results["failed"] += 1
                print(f"Failed to create vendor: {vendor_name}. Status code: {response.status_code}, Error: {response.text}")

    print(f"Vendor creation summary: {vendor_creation_results['created']} created, {len(existing_vendor_names)} already existed, {vendor_creation_results['failed']} failed.")

    # Refresh the list of vendors to get IDs for all
    try:
        all_vendors_list = get_vendors()
        vendor_map = {vendor['name']: vendor['id'] for vendor in all_vendors_list}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching vendors from Spoolman after creation: {e}")
        return

    # --- Filament Processing ---
    print("Processing filaments...")
    # Get all existing filaments from Spoolman for an efficient check
    try:
        existing_filaments_list = get_filaments()
        existing_filament_names = {f['name'] for f in existing_filaments_list}
        print(f"Found {len(existing_filament_names)} existing filaments in Spoolman.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching filaments from Spoolman: {e}")
        return

    filament_results = {"created": 0, "skipped": 0, "failed": 0}
    for item in filaments_data:
        filament_name = item.get("name")
        if not filament_name:
            continue  # Skip items without a name

        # Check if the filament already exists using the pre-fetched set
        if filament_name in existing_filament_names:
            filament_results["skipped"] += 1
            continue

        # Get vendor ID from our map
        manufacturer_name = item.get("manufacturer")
        if not manufacturer_name or manufacturer_name not in vendor_map:
            print(f"Skipping filament '{filament_name}' because its vendor '{manufacturer_name}' was not found or created.")
            filament_results["failed"] += 1
            continue
        vendor_id = vendor_map[manufacturer_name]

        # Get material ID from our map
        material_name = item.get("material")
        if not material_name or material_name not in material_map:
            print(f"Skipping filament '{filament_name}' because its material '{material_name}' was not found or created.")
            filament_results["failed"] += 1
            continue
        material_id = material_map[material_name]

        # Ensure spool_weight is greater than 0
        spool_weight = item.get("spool_weight", 1)
        if not isinstance(spool_weight, (int, float)) or spool_weight <= 0:
            spool_weight = 1

        filament = {
            "name": filament_name,
            "density": item.get("density", 1.23),  # Common PLA density as a fallback
            "weight": item.get("weight", 0),
            "spool_weight": spool_weight,
            "diameter": item.get("diameter", 1.75),
            "settings_extruder_temp": item.get("extruder_temp", 200),
            "settings_bed_temp": item.get("bed_temp", 60),
            "color_hex": item.get("color_hex"),
            "external_id": item.get("id"),
            "vendor_id": vendor_id,
            "material_id": material_id
        }

        # Send the POST request to create the filament
        response = create_filament(filament)
        if 200 <= response.status_code < 300:
            filament_results["created"] += 1
        else:
            filament_results["failed"] += 1
            print(f"Failed to create filament '{filament_name}'. Status: {response.status_code}, Error: {response.text}")

    print(f"Filament processing summary: {filament_results['created']} created, {filament_results['skipped']} skipped (already existed), {filament_results['failed']} failed.")
    print("All data processed.")

# Function to delete all vendors and filaments
def delete_all_data():
    # Fetch and delete all filaments
    try:
        filaments = get_filaments()
        print(f"Found {len(filaments)} filaments to delete.")
        for filament in filaments:
            filament_id = filament['id']
            response = delete_filament(filament_id)
            if 200 <= response.status_code < 300:
                print(f"Successfully deleted filament: {filament['name']} (ID: {filament_id})")
            else:
                print(f"Failed to delete filament: {filament['name']} (ID: {filament_id}). Status code: {response.status_code}, Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch filaments to delete: {e}")

    # Fetch and delete all materials
    try:
        materials = get_materials()
        print(f"Found {len(materials)} materials to delete.")
        for material in materials:
            material_id = material['id']
            response = delete_material(material_id)
            if 200 <= response.status_code < 300:
                print(f"Successfully deleted material: {material['name']} (ID: {material_id})")
            else:
                print(f"Failed to delete material: {material['name']} (ID: {material_id}). Status code: {response.status_code}, Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch materials to delete: {e}")

    # Fetch and delete all vendors
    try:
        vendors = get_vendors()
        print(f"Found {len(vendors)} vendors to delete.")
        for vendor in vendors:
            vendor_id = vendor['id']
            response = delete_vendor(vendor_id)
            if 200 <= response.status_code < 300:
                print(f"Successfully deleted vendor: {vendor['name']} (ID: {vendor_id})")
            else:
                print(f"Failed to delete vendor: {vendor['name']} (ID: {vendor_id}). Status code: {response.status_code}, Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch vendors to delete: {e}")

    print("Deletion process finished.")

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
