"""
D'Addario String Tension Pro

It's back---got the beta email notice on 2024-06-12.
"""
import re
from urllib.parse import urlsplit

import requests

url_app = "https://www.daddario.com/string-tension-pro"
url_rec_js = (
    "https://embed.cartfulsolutions.com/daddario-string-tension-finder/recommendation.min.js"
)
url_data = (
    "https://embed.cartfulsolutions.com/daddario-string-tension-finder/data/strings_dataset.json"
)

r = requests.get(url_app)
r.raise_for_status()
p = urlsplit(url_rec_js)
assert p.netloc in r.text
assert p.path in r.text

r = requests.get(url_rec_js)
data_urls = re.findall(
    r"\"(https://[a-z\./]*/daddario-string-tension-finder/data/[a-z_\./]*)\"", r.text
)
data_urls.sort()
print("data URLs:")
print("\n".join(f"- {url}" for url in data_urls))
assert len(data_urls) > 0
assert url_data in data_urls

r = requests.get(url_data)
r.raise_for_status()
raw_data = r.json()

# List of entries, for example:
#
#  {'SetItemNumber': 'EJ13',
#   'ComponentItemNumber': 'PL011',
#   'SubComponent': 'U1AGFPL011-NP',
#   'SequenceNumber': 1,
#   'ItemClassPosition1': 'A',
#   'ItemClassPosition2': 'B',
#   'ItemClassPosition3': 'J',
#   'ItemClassPosition4': 'A',
#   'SizeInInches(gauge)': 11,
#   'SizeInMillimeters(gauge)': 279.4,
#   'StringConstruction': 'Plain Steel',
#   'MassPerUnitLength': 2.68184e-05,
#   'Instrument': 'Acoustic Guitar',
#   'Material': 'Tin Coated Steel',
#   'EndType': 'Small Ball End'},
#
# Individual string data is duplicated, for the sake of sets.
