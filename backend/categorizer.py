"""
Categorization Engine — rule-based keyword matching.

No ML required. Each transaction description is lowercased and
checked against keyword lists. Easily extensible: add new keywords
to RULES below. Priority is top-to-bottom (first match wins).
"""

from typing import List, Dict, Any

# ─── Rules — order matters: first match wins ──────────────────────────────────

RULES: List[tuple[str, List[str]]] = [
    ("Rent", [
        "rent", "house rent", "pg rent", "landlord",
        "accommodation", "hostel fee",
    ]),
    ("Food", [
        "swiggy", "zomato", "dominos", "pizza", "burger", "kfc", "mcdonalds",
        "mcdonald", "subway", "barbeque", "bbq", "restaurant", "cafe", "coffee",
        "starbucks", "chai", "darshini", "mess", "canteen", "food",
        "big basket", "bigbasket", "zepto", "blinkit", "instamart",
        "fresh", "groceries", "grocery", "supermarket", "d-mart", "dmart",
        "more superstore", "reliance fresh", "namdhari",
    ]),
    ("Transport", [
        "uber", "ola", "rapido", "namma metro", "bmtc", "ksrtc", "irctc",
        "indian railway", "indigo", "spicejet", "air india", "goair",
        "petrol", "fuel", "fastag", "toll", "parking",
        "cab", "auto", "bike taxi", "shuttle",
    ]),
    ("Entertainment", [
        "netflix", "prime video", "hotstar", "disney", "zee5", "sonyliv",
        "spotify", "youtube", "apple music", "jiosaavn", "gaana",
        "bookmyshow", "pvr", "inox", "cinepolis", "movie", "concert",
        "gaming", "steam", "playstation", "xbox",
    ]),
    ("Shopping", [
        "amazon", "flipkart", "myntra", "ajio", "meesho", "nykaa", "purplle",
        "reliance digital", "croma", "vijay sales", "decathlon",
        "max fashion", "pantaloons", "lifestyle", "shoppers stop",
        "h&m", "zara", "uniqlo", "westside",
    ]),
    ("Utilities", [
        "bescom", "bwssb", "tangedco", "msedcl", "electricity", "water bill",
        "gas bill", "piped gas", "mahanagar gas", "indane", "bharat gas",
        "airtel", "jio", "vodafone", "vi", "bsnl", "tata sky", "dish tv",
        "broadband", "internet", "dth", "recharge", "mobile bill",
    ]),
    ("Health", [
        "apollo", "medplus", "netmeds", "1mg", "pharmeasy", "pharmacy",
        "hospital", "clinic", "doctor", "consult", "lab test", "diagnostic",
        "healthspring", "cult.fit", "curefit", "gym", "fitness", "yoga",
        "dental", "vision", "eye care", "optician",
    ]),
    ("Finance", [
        "insurance", "lic", "hdfc life", "icici pru", "sip", "mutual fund",
        "zerodha", "groww", "coin", "loan emi", "emi payment",
        "credit card bill", "repayment",
    ]),
    ("Education", [
        "udemy", "coursera", "unacademy", "byju", "vedantu", "upgrad",
        "tuition", "school fee", "college fee", "books", "stationery",
    ]),
    ("Travel", [
        "hotel", "oyo", "makemytrip", "goibibo", "yatra", "airbnb",
        "treebo", "fabhotels", "resort", "lodge", "guesthouse",
        "tour package", "holiday",
    ]),
]

DEFAULT_CATEGORY = "Others"


# ─── Public API ───────────────────────────────────────────────────────────────

def categorize_transactions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add a 'category' field to each transaction dict in-place.
    Returns the same list with categories populated.
    """
    for txn in transactions:
        txn["category"] = _categorize(txn.get("description", ""))
    return transactions


def categorize_one(description: str) -> str:
    """Categorize a single transaction description string."""
    return _categorize(description)


# ─── Internal ─────────────────────────────────────────────────────────────────

def _categorize(description: str) -> str:
    desc_lower = description.lower()
    for category, keywords in RULES:
        if any(kw in desc_lower for kw in keywords):
            return category
    return DEFAULT_CATEGORY


# ─── CLI test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        "SWIGGY ORDER #84729",
        "NETFLIX SUBSCRIPTION",
        "UBER TRIP MUMBAI",
        "BESCOM ELECTRICITY BILL",
        "HDFC LIFE INSURANCE PREMIUM",
        "AMAZON.IN PURCHASE",
        "UNKNOWN VENDOR XYZ",
        "RENT PAYMENT MARCH",
    ]
    for tc in test_cases:
        print(f"  {tc:40s} → {categorize_one(tc)}")
