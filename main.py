import requests
import json
import os
import argparse
from dotenv import load_dotenv

class SpoolmanImporter:
    def __init__(self, spoolman_url, source_url):
        """
        Initialises the SpoolmanImporter with the necessary URLs.

        Args:
            spoolman_url (str): The base URL of the Spoolman API.
            source_url (str): The URL to the source filaments.json file.
        """
        if not spoolman_url:
            raise ValueError("Spoolman URL must be provided via .env file or --spoolman-url argument.")
        self.spoolman_url = spoolman_url
        self.source_url = source_url

    def _post(self, endpoint, data):
        """Helper function to send a POST request."""
        url = f"{self.spoolman_url}/api/v1/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        return requests.post(url, headers=headers, data=json.dumps(data))

    def _get(self, endpoint):
        """Helper function to send a GET request."""
        url = f"{self.spoolman_url}/api/v1/{endpoint}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def _delete(self, endpoint, item_id):
        """Helper function to send a DELETE request."""
        url = f"{self.spoolman_url}/api/v1/{endpoint}/{item_id}"
        return requests.delete(url)

    def create_filament(self, filament):
        return self._post("filament", filament)

    def create_vendor(self, vendor):
        return self._post("vendor", vendor)

    def get_vendors(self):
        return self._get("vendor")

    def get_filaments(self):
        return self._get("filament")

    def delete_vendor(self, vendor_id):
        return self._delete("vendor", vendor_id)

    def delete_filament(self, filament_id):
        return self._delete("filament", filament_id)

    def create_data(self):
        """Fetches data from the source and creates vendors and filaments in Spoolman."""
        print(f"Fetching filament data from {self.source_url}...")
        try:
            response = requests.get(self.source_url)
            response.raise_for_status()
            filaments_data = response.json()
            print(f"Found {len(filaments_data)} filament definitions.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching filament data from source URL: {e}")
            return

        # --- Vendor Processing ---
        print("Processing vendors...")
        try:
            existing_vendors_list = self.get_vendors()
            existing_vendor_names = {vendor['name'] for vendor in existing_vendors_list}
            print(f"Found {len(existing_vendor_names)} existing vendors in Spoolman.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching vendors from Spoolman: {e}")
            return

        all_vendor_names = {item["manufacturer"] for item in filaments_data if item.get("manufacturer")}
        vendors_to_create_names = all_vendor_names - existing_vendor_names

        vendor_creation_results = {"created": 0, "failed": 0}
        if vendors_to_create_names:
            print(f"Creating {len(vendors_to_create_names)} new vendors...")
            for vendor_name in vendors_to_create_names:
                response = self.create_vendor({"name": vendor_name})
                if 200 <= response.status_code < 300:
                    vendor_creation_results["created"] += 1
                else:
                    vendor_creation_results["failed"] += 1
                    print(f"Failed to create vendor: {vendor_name}. Status: {response.status_code}, Error: {response.text}")
        
        print(f"Vendor creation summary: {vendor_creation_results['created']} created, {len(existing_vendor_names)} already existed, {vendor_creation_results['failed']} failed.")

        try:
            all_vendors_list = self.get_vendors()
            vendor_map = {vendor['name']: vendor['id'] for vendor in all_vendors_list}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching vendors from Spoolman after creation: {e}")
            return

        # --- Filament Processing ---
        print("Processing filaments...")
        try:
            existing_filaments_list = self.get_filaments()
            existing_filament_names = {f['name'] for f in existing_filaments_list}
            print(f"Found {len(existing_filament_names)} existing filaments in Spoolman.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching filaments from Spoolman: {e}")
            return

        filament_results = {"created": 0, "skipped": 0, "failed": 0}
        for item in filaments_data:
            filament_name = item.get("name")
            if not filament_name or filament_name in existing_filament_names:
                if filament_name:
                    filament_results["skipped"] += 1
                continue

            manufacturer_name = item.get("manufacturer")
            if not manufacturer_name or manufacturer_name not in vendor_map:
                print(f"Skipping filament '{filament_name}' because its vendor '{manufacturer_name}' was not found or created.")
                filament_results["failed"] += 1
                continue
            
            spool_weight = item.get("spool_weight", 1)
            if not isinstance(spool_weight, (int, float)) or spool_weight <= 0:
                spool_weight = 1

            filament = {
                "name": filament_name,
                "material": item.get("material"),
                "density": item.get("density", 1.23),
                "weight": item.get("weight", 0),
                "spool_weight": spool_weight,
                "diameter": item.get("diameter", 1.75),
                "settings_extruder_temp": item.get("extruder_temp", 200),
                "settings_bed_temp": item.get("bed_temp", 60),
                "color_hex": item.get("color_hex"),
                "external_id": item.get("id"),
                "vendor_id": vendor_map[manufacturer_name]
            }

            response = self.create_filament(filament)
            if 200 <= response.status_code < 300:
                filament_results["created"] += 1
            else:
                filament_results["failed"] += 1
                print(f"Failed to create filament '{filament_name}'. Status: {response.status_code}, Error: {response.text}")

        print(f"Filament processing summary: {filament_results['created']} created, {filament_results['skipped']} skipped (already existed), {filament_results['failed']} failed.")
        print("All data processed.")

    def delete_all_data(self):
        """Deletes all filaments and vendors from Spoolman."""
        try:
            filaments = self.get_filaments()
            print(f"Found {len(filaments)} filaments to delete.")
            for filament in filaments:
                response = self.delete_filament(filament['id'])
                if 200 <= response.status_code < 300:
                    print(f"Successfully deleted filament: {filament['name']} (ID: {filament['id']})")
                else:
                    print(f"Failed to delete filament: {filament['name']} (ID: {filament['id']}). Status: {response.status_code}, Error: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Could not fetch filaments to delete: {e}")

        try:
            vendors = self.get_vendors()
            print(f"Found {len(vendors)} vendors to delete.")
            for vendor in vendors:
                response = self.delete_vendor(vendor['id'])
                if 200 <= response.status_code < 300:
                    print(f"Successfully deleted vendor: {vendor['name']} (ID: {vendor['id']})")
                else:
                    print(f"Failed to delete vendor: {vendor['name']} (ID: {vendor['id']}). Status: {response.status_code}, Error: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Could not fetch vendors to delete: {e}")

        print("Deletion process finished.")

    def replace_data(self):
        """Performs a full replacement of Spoolman data from the source."""
        print("Replacing all data. This will first delete all existing filaments and vendors.")
        self.delete_all_data()
        print("\nDeletion complete. Now creating new data.")
        self.create_data()

def main():
    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(description="Manage Spoolman data by importing from a source URL.")
    parser.add_argument(
        "action",
        choices=["create", "delete", "replace"],
        help="Action to perform: 'create' to add new data, 'delete' to remove all data, 'replace' to do a full delete and then create."
    )
    parser.add_argument(
        "--spoolman-url",
        type=str,
        default=os.getenv("SPOOLMAN_URL"),
        help="URL of the Spoolman instance. Overrides the SPOOLMAN_URL from .env file."
    )
    parser.add_argument(
        "--source-url",
        type=str,
        default="https://donkie.github.io/SpoolmanDB/filaments.json",
        help="URL of the source filaments.json file."
    )
    args = parser.parse_args()

    try:
        importer = SpoolmanImporter(spoolman_url=args.spoolman_url, source_url=args.source_url)
        
        if args.action == "create":
            importer.create_data()
        elif args.action == "delete":
            importer.delete_all_data()
        elif args.action == "replace":
            importer.replace_data()

    except ValueError as e:
        print(f"Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"A network error occurred: {e}")

if __name__ == "__main__":
    main()
