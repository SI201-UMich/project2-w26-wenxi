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

    results = []
    seen = set()

    #Extract listing IDs and match with titles from button aria-labels
    for a in soup.find_all("a", href=True):
        # Match both /rooms/ and /rooms/plus/ patterns
        match = re.search(r"/rooms/(?:plus/)?(\d+)", a["href"])
        if not match:
            continue
        listing_id = match.group(1)

        if listing_id in seen:
            continue

        # Find the nearest button with 'Add to wishlist' aria-label
        title = ""
        container = a.parent

        # Search in parent containers for the wishlist button
        for level in range(5):
            if container:
                button = container.find("button", attrs={"aria-label": re.compile(r"Add to wishlist:")})
                if button:
                    title = button["aria-label"].replace("Add to wishlist:", "").strip()
                    break
                container = container.parent

        if title and listing_id:
            seen.add(listing_id)
            results.append((title, listing_id))

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

    # Check line by line for specific valid/status patterns first
    for line in texts.splitlines():
        line = line.strip()

        # Check for year format with STR suffix
        if re.search(r"20\d{2}-00\d{4}STR", line):
            policy_num = re.search(r"20\d{2}-00\d{4}", line).group()
            break
        # Check for STR-000XXXX format
        if re.search(r"STR-000\d{4}", line):
            policy_num = re.search(r"STR-000\d{4}", line).group()
            break
        # Check for pending status
        if re.search(r"\bpending\b", line, re.IGNORECASE):
            policy_num = "Pending"
            break
        # Check for exempt status
        if re.search(r"\bexempt\b", line, re.IGNORECASE):
            policy_num = "Exempt"
            break

    # If no valid pattern found, check for generic "Policy number:" (may span lines)
    # This will catch invalid formats like plain numbers
    if policy_num == "Exempt":
        policy_match = re.search(r"Policy number:\s*(\d+)", texts, re.IGNORECASE)
        if policy_match:
            policy_num = policy_match.group(1)

    #host type
    host_type = "regular"
    if soup.find(string=re.compile(r"Superhost", re.IGNORECASE)):
        host_type = "Superhost"
    
    #host name "Hosted by"
    host_name = ""
    # Look specifically in h2 tags for clean extraction
    for tag in soup.find_all("h2"):
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
 
    """Check subtitle specifically"""
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
 
    """location_rating"""
    location_rating = 0.0
    """Look for "Location" followed by a rating number"""
    # Use \s* to allow zero or more whitespace characters
    m = re.search(r"Location\s*(\d+\.\d+)", soup.get_text())
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

    """Returns list of 7-element tuples with full listing info."""
    listings = load_listing_results(html_path)
    database = []
    for title, listing_id in listings:
        details = get_listing_details(listing_id)
        d = details[listing_id]
        database.append((
            title,
            listing_id,
            d["policy_number"],
            d["host_type"],
            d["host_name"],
            d["room_type"],
            d["location_rating"],
        ))
    return database
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
    """Writes sorted (desc by location_rating) data to CSV."""
    sorted_data = sorted(data, key=lambda x: x[6], reverse=True)
    #open file
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Listing Title", "Listing ID", "Policy Number",
                         "Host Type", "Host Name", "Room Type", "Location Rating"])
        for row in sorted_data:
            writer.writerow(row)
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
    """Returns dict of avg location_rating per room_type, excluding 0.0 ratings."""
    totals = {}
    counts = {}
    for row in data:
        room_type = row[5]
        rating = row[6]
        if rating == 0.0:
            continue
        totals[room_type] = totals.get(room_type, 0.0) + rating
        counts[room_type] = counts.get(room_type, 0) + 1
    return {rt: round(totals[rt] / counts[rt], 2) for rt in totals}
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
    
    """Returns list of listing_ids with invalid policy number format."""
    valid_pattern = re.compile(r"^(20\d{2}-00\d{4}|STR-000\d{4})$")
    invalid_ids = []
    for row in data:
        listing_id = row[1]
        policy = row[2]
        if policy in ("Pending", "Exempt"):
            continue
        if not valid_pattern.match(policy):
            invalid_ids.append(listing_id)
    return invalid_ids
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

    url = f"https://scholar.google.com/scholar?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    titles = []
    for tag in soup.find_all("h3", class_="gs_rt"):
        # strip any [PDF], [HTML] labels and get just the title text
        for label in tag.find_all("span"):
            label.decompose()
        titles.append(tag.get_text(strip=True))
    
    return titles
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
        self.assertEqual(len(self.listings), 18)
        self.assertEqual(self.listings[0], ("Loft in Mission District", "1944564"))

    def test_get_listing_details(self):
        html_list = ["467507", "1550913", "1944564", "4614763", "6092596"]

        # TODO: Call get_listing_details() on each listing id above and save results in a list.

        # TODO: Spot-check a few known values by opening the corresponding listing_<id>.html files.
        # 1) Check that listing 467507 has the correct policy number "STR-0005349".
        # 2) Check that listing 1944564 has the correct host type "Superhost" and room type "Entire Room".
        # 3) Check that listing 1944564 has the correct location rating 4.9.
        results = [get_listing_details(lid) for lid in html_list]
        self.assertEqual(results[0]["467507"]["policy_number"], "STR-0005349")
        self.assertEqual(results[2]["1944564"]["host_type"], "Superhost")
        self.assertEqual(results[2]["1944564"]["room_type"], "Entire Room")
        self.assertEqual(results[2]["1944564"]["location_rating"], 4.9)

    def test_create_listing_database(self):
        # TODO: Check that each tuple in detailed_data has exactly 7 elements:
        # (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)

        # TODO: Spot-check the LAST tuple is ("Guest suite in Mission District", "467507", "STR-0005349", "Superhost", "Jennifer", "Entire Room", 4.8).
        for row in self.detailed_data:
            self.assertEqual(len(row), 7)
        self.assertEqual(self.detailed_data[-1], ("Guest suite in Mission District", "467507", "STR-0005349", "Superhost", "Jennifer", "Entire Room", 4.8))

    def test_output_csv(self):
        out_path = os.path.join(self.base_dir, "test.csv")

        # TODO: Call output_csv() to write the detailed_data to a CSV file.
        # TODO: Read the CSV back in and store rows in a list.
        # TODO: Check that the first data row matches ["Guesthouse in San Francisco", "49591060", "STR-0000253", "Superhost", "Ingrid", "Entire Room", "5.0"].
        out_path = os.path.join(self.base_dir, "test.csv")
        output_csv(self.detailed_data, out_path)
        with open(out_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            first_row = next(reader)
        self.assertEqual(first_row, ["Guesthouse in San Francisco", "49591060", "STR-0000253", "Superhost", "Ingrid", "Entire Room", "5.0"])
        os.remove(out_path)

    def test_avg_location_rating_by_room_type(self):
        # TODO: Call avg_location_rating_by_room_type() and save the output.
        # TODO: Check that the average for "Private Room" is 4.9.
        avgs = avg_location_rating_by_room_type(self.detailed_data)
        self.assertEqual(avgs["Private Room"], 4.9)

    def test_validate_policy_numbers(self):
        # TODO: Call validate_policy_numbers() on detailed_data and save the result into a variable invalid_listings.
        # TODO: Check that the list contains exactly "16204265" for this dataset.
        invalid_listings = validate_policy_numbers(self.detailed_data)
        self.assertEqual(invalid_listings, ["16204265"])


def main():
    detailed_data = create_listing_database(os.path.join("html_files", "search_results.html"))
    output_csv(detailed_data, "airbnb_dataset.csv")


if __name__ == "__main__":
    main()
    unittest.main(verbosity=2)