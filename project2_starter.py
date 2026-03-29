# SI 201 HW4 (Library Checkout System)
# Your name: Wen Xi Hu
# Your student id: 61796814
# Your email: wxh@umich.edu
# Who or what you worked with on this homework (including generative AI like ChatGPT):
# If you worked with generative AI also add a statement for how you used it.
# e.g.:
# Asked ChatGPT for hints on debugging and for suggestions on overall code structure
#
# Did your use of GenAI on this assignment align with your goals and guidelines in your Gen AI contract? If not, why?
# I used GenAI for hints on debugging and suggestions on code structure efficiencya and review on debugging tips, which all align with my goals and guidelines since I am not aimlessly copying code and actually take in what is produced.
# --- ARGUMENTS & EXPECTED RETURN VALUES PROVIDED --- #
# --- SEE INSTRUCTIONS FOR FULL DETAILS ON METHOD IMPLEMENTATION --- #

from bs4 import BeautifulSoup
import re
import os
import csv
import unittest
import requests  # kept for extra credit parity


# IMPORTANT NOTE:
"""
If you are getting "encoding errors" while trying to open, read, or write from a file, add the following argument to any of your open() functions:
    encoding="utf-8-sig"
"""


def load_listing_results(html_path) -> list[tuple]:
    """
    Load file data from html_path and parse through it to find listing titles and listing ids.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples containing (listing_title, listing_id)
    """
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================

    #Load file and parse
    with open(html_path, "r", encoding="utf-8-sig") as f:
        soup = BeautifulSoup(f, "html.parser")

    seen = set()
    results = []

    #regex from href to get id
    for a in soup.find_all("a", href = True):
        match = re.search(r"/rooms/(\d+)", a["href"])
        if not match:
            continue
        listing_id = match.group(1)

        title = a.get("aria-label", "").strip()
        if not title:
            tag = a.find(["h3", "div", "span"])
            title = tag.get_text(strip=True) if tag else ""
        if listing_id not in seen and title:
            seen.add(listing_id)
            results.append((title,listing_id))
    
    return results
        

    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def get_listing_details(listing_id) -> dict:
    """
    Parse through listing_<id>.html to extract listing details.

    Args:
        listing_id (str): The listing id of the Airbnb listing

    Returns:
        dict: Nested dictionary in the format:
        {
            "<listing_id>": {
                "policy_number": str,
                "host_type": str,
                "host_name": str,
                "room_type": str,
                "location_rating": float
            }
        }
    """
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    
    html_path = f"html_files/listing_{listing_id}.html"
    with open(html_path, "r", encoding="utf-8-sig") as f:
        soup = BeautifulSoup(f, "html.parser")

    #policy number
    policy_num = "Exempt"
    texts = soup.get_text(separator="\n")
    for line in texts.splitlines():
        line = line.strip()
        
        if re.search(r"20\d{2}-00\d{4}STR", line):
            policy_num = re.search(r"20\d{2}-00\d{4}").group()
            break
        if re.search(r"STR-000\d{4}", line):
            policy_num = re.search(r"STR-000\d{4}", line).group()
            break
        if re.search(r"pending", line, re.IGNORECASE):
            policy_num = "Pending"
            break

    #host type
    host_type = "regular"
    if soup.find(string=re.compile(r"Superhost", re.IGNORECASE)):
        host_type = "Superhost"
    
    #host name "Hosted by"
    host_name = ""
    #common host name patterns
    for tag in soup.find_all(["div", "span", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if re.match(r"^Hosted by (.+)$", text, re.IGNORECASE):
            host_name = re.match(r"^Hosted by (.+)$", text, re.IGNORECASE).group(1)
            break
    if not host_name:
        # fallback: find any tag with "Hosted by"
        match = re.search(r"Hosted by ([^\n<]+)", soup.get_text())
        if match:
            host_name = match.group(1).strip()
    
    #room_type
    subtitle_text = ""
    for tag in soup.find_all(["h2", "h3", "div", "span"]):
        t = tag.get_text(strip=True)
        if re.search(r"(private|shared|entire|room|suite|home|loft|apartment)", t, re.IGNORECASE):
            subtitle_text = t
            break
 
    full_text = soup.get_text()
    if re.search(r"private", full_text[:3000], re.IGNORECASE):
        room_type = "Private Room"
    elif re.search(r"shared", full_text[:3000], re.IGNORECASE):
        room_type = "Shared Room"
    else:
        room_type = "Entire Room"
 
    #Check subtitle specifically
    for tag in soup.find_all(["h2", "h3"]):
        t = tag.get_text(strip=True)
        if "Private" in t:
            room_type = "Private Room"
            break
        elif "Shared" in t:
            room_type = "Shared Room"
            break
        elif any(w in t for w in ["Entire", "Home", "Loft", "Apartment", "Suite", "Guesthouse", "Condo"]):
            room_type = "Entire Room"
            break
 
    #location_rating
    location_rating = 0.0
    # Look for "Location" near a rating number
    for tag in soup.find_all(["div", "span"]):
        t = tag.get_text(strip=True)
        if re.match(r"^Location$", t, re.IGNORECASE):
            # Try to find next sibling or parent's next text
            parent = tag.parent
            if parent:
                parent_text = parent.get_text(strip=True)
                m = re.search(r"Location\s+([\d.]+)", parent_text)
                if m:
                    location_rating = float(m.group(1))
                    break
 
    if location_rating == 0.0:
        m = re.search(r"Location\s+([\d.]+)", soup.get_text())
        if m:
            location_rating = float(m.group(1))
 
    return {
        listing_id: {
            "policy_number": policy_num,
            "host_type": host_type,
            "host_name": host_name,
            "room_type": room_type,
            "location_rating": location_rating,
        }
    }
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def create_listing_database(html_path) -> list[tuple]:
    """
    Use prior functions to gather all necessary information and create a database of listings.

    Args:
        html_path (str): The path to the HTML file containing the search results

    Returns:
        list[tuple]: A list of tuples. Each tuple contains:
        (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)
    """
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    pass
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def output_csv(data, filename) -> None:
    """
    Write data to a CSV file with the provided filename.

    Sort by Location Rating (descending).

    Args:
        data (list[tuple]): A list of tuples containing listing information
        filename (str): The name of the CSV file to be created and saved to

    Returns:
        None
    """
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    pass
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def avg_location_rating_by_room_type(data) -> dict:
    """
    Calculate the average location_rating for each room_type.

    Excludes rows where location_rating == 0.0 (meaning the rating
    could not be found in the HTML).

    Args:
        data (list[tuple]): The list returned by create_listing_database()

    Returns:
        dict: {room_type: average_location_rating}
    """
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    pass
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


def validate_policy_numbers(data) -> list[str]:
    """
    Validate policy_number format for each listing in data.
    Ignore "Pending" and "Exempt" listings.

    Args:
        data (list[tuple]): A list of tuples returned by create_listing_database()

    Returns:
        list[str]: A list of listing_id values whose policy numbers do NOT match the valid format
    """
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    pass
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


# EXTRA CREDIT
def google_scholar_searcher(query):
    """
    EXTRA CREDIT

    Args:
        query (str): The search query to be used on Google Scholar
    Returns:
        List of titles on the first page (list)
    """
    # TODO: Implement checkout logic following the instructions
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    pass
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================


class TestCases(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.search_results_path = os.path.join(self.base_dir, "html_files", "search_results.html")

        self.listings = load_listing_results(self.search_results_path)
        self.detailed_data = create_listing_database(self.search_results_path)

    def test_load_listing_results(self):
        # TODO: Check that the number of listings extracted is 18.
        # TODO: Check that the FIRST (title, id) tuple is  ("Loft in Mission District", "1944564").
        pass

    def test_get_listing_details(self):
        html_list = ["467507", "1550913", "1944564", "4614763", "6092596"]

        # TODO: Call get_listing_details() on each listing id above and save results in a list.

        # TODO: Spot-check a few known values by opening the corresponding listing_<id>.html files.
        # 1) Check that listing 467507 has the correct policy number "STR-0005349".
        # 2) Check that listing 1944564 has the correct host type "Superhost" and room type "Entire Room".
        # 3) Check that listing 1944564 has the correct location rating 4.9.
        pass

    def test_create_listing_database(self):
        # TODO: Check that each tuple in detailed_data has exactly 7 elements:
        # (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)

        # TODO: Spot-check the LAST tuple is ("Guest suite in Mission District", "467507", "STR-0005349", "Superhost", "Jennifer", "Entire Room", 4.8).
        pass

    def test_output_csv(self):
        out_path = os.path.join(self.base_dir, "test.csv")

        # TODO: Call output_csv() to write the detailed_data to a CSV file.
        # TODO: Read the CSV back in and store rows in a list.
        # TODO: Check that the first data row matches ["Guesthouse in San Francisco", "49591060", "STR-0000253", "Superhost", "Ingrid", "Entire Room", "5.0"].

        os.remove(out_path)

    def test_avg_location_rating_by_room_type(self):
        # TODO: Call avg_location_rating_by_room_type() and save the output.
        # TODO: Check that the average for "Private Room" is 4.9.
        pass

    def test_validate_policy_numbers(self):
        # TODO: Call validate_policy_numbers() on detailed_data and save the result into a variable invalid_listings.
        # TODO: Check that the list contains exactly "16204265" for this dataset.
        pass


def main():
    detailed_data = create_listing_database(os.path.join("html_files", "search_results.html"))
    output_csv(detailed_data, "airbnb_dataset.csv")


if __name__ == "__main__":
    main()
    unittest.main(verbosity=2)