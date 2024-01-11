import pandas as pd
from pypdf import PdfReader

reader = PdfReader("C:/Users/zmoon/OneDrive/h/music/ghs_acoustic_guitar_string_guide.pdf")

page = reader.pages[2]
text = page.extract_text()

# First two header lines,
# then seems that the UW's come out first,
# then the IDs, with last one having the UW column header in it
uws = []
ids = []
last = False
for i, line in enumerate(text.splitlines()):
    print(f"=={i:03d}=={line}==")

    line = line.strip()

    if line in {"By Individual String"} or line.startswith("Play With The Best"):
        continue

    if "Unit Weight " in line:
        line = line[: line.index("Unit Weight ")]
        last = True

    if line.startswith("."):
        if len(line) == 9:
            uw = line
        elif len(line) > 9:
            uw, first_id = line[:9], line[9:]
            ids.insert(0, first_id)
        else:
            raise AssertionError(line)
        uws.append(uw)
    else:
        ids.append(line)

    if last:
        break

for i, id_ in enumerate(ids):
    if " 1/2" in id_:
        ids[i] = id_.replace(" 1/2", "5")

assert len(ids) == len(uws)

df = pd.DataFrame({"id": ids, "uw": uws})

print(df)
