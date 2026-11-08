import sys, re, json, argparse, requests

# python sky-garden.py 'NAME' [radius_deg] [--savename NAME] [--nstars N]
# python sky-garden.py RA DEC radius_deg [--savename NAME] [--nstars N]

# writes NAME.json and NAME.csv, loadable with Upload

NSTARS = 50
TAP = "https://gea.esac.esa.int/tap-server/tap/sync"
SESAME = ["https://cds.unistra.fr/cgi-bin/nph-sesame/-op/NSV?", "http://vizier.cfa.harvard.edu/viz-bin/nph-sesame/-op/NSV?"]

def mast(name):
    req = dict(service = "Mast.Name.Lookup", params = dict(input = name, format = "json"))
    r = requests.post("https://mast.stsci.edu/api/v0/invoke", data = dict(request = json.dumps(req)), timeout = 30).json()
    c = r["resolvedCoordinate"][0]
    return float(c["ra"]), float(c["decl"])

def sesame(url, name):
    txt = requests.get(url + name, timeout = 20).text
    m = re.search(r"%J\s+([\d.]+)\s+([+-]?[\d.]+)", txt)
    if not m:
        raise ValueError("not found")
    return float(m.group(1)), float(m.group(2))

def resolve(name):
    # name servers in turn: STScI MAST, CDS Sesame, Harvard Sesame
    tries = [("mast.stsci.edu", lambda: mast(name))] + [(u.split("/")[2], lambda u = u: sesame(u, name)) for u in SESAME]
    for host, fn in tries:
        try:
            return fn()
        except Exception as e:
            print("name server failed:", host, type(e).__name__)
    sys.exit("no name server answered, give the coordinates instead: python " + sys.argv[0] + " RA DEC RADIUS")

def gaia(ra, dec, radius, nstars):
    rows = []
    for mag in [12, 14, 17]:
        q = f"SELECT TOP {nstars} ra, dec, phot_g_mean_mag, bp_rp FROM gaiadr3.gaia_source WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {radius})) AND phot_g_mean_mag < {mag} ORDER BY phot_g_mean_mag"
        r = requests.get(TAP, params = dict(REQUEST = "doQuery", LANG = "ADQL", FORMAT = "csv", QUERY = q), timeout = 300)
        r.raise_for_status()
        rows = [l.split(",") for l in r.text.strip().split("\n")[1:]]
        print("G <", mag, ":", len(rows), "stars")
        if len(rows) >= min(nstars, 150):
            break
    if not rows:
        sys.exit("no Gaia stars found")
    return [[float(c[0]), float(c[1]), float(c[2]), (float(c[3]) if c[3] != "" else None)] for c in rows]

def number(x):
    try:
        float(x)
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs = "+")
    ap.add_argument("--savename")
    ap.add_argument("--nstars", type = int, default = NSTARS)
    args = ap.parse_args()
    a = args.target
    if len(a) == 3 and all(number(x) for x in a):
        name, ra, dec, radius = f"{a[0]} {a[1]}", float(a[0]), float(a[1]), float(a[2])
    elif not number(a[0]):
        radius = float(a.pop()) if len(a) > 1 and number(a[-1]) else 0.3
        name = " ".join(a)
        ra, dec = resolve(name)
    else:
        sys.exit(__doc__)
    ra, dec = round(ra, 4), round(dec, 4)
    base = args.savename or re.sub(r"\W+", "_", name).strip("_")
    print("field:", ra, dec, radius)
    stars = gaia(ra, dec, radius, args.nstars)
    json.dump(dict(name = args.savename or name, ra = ra, dec = dec, radius = radius, stars = stars), open(base + ".json", "w"), separators = (",", ":"))
    print("saved", base + ".json", len(stars), "stars")
    with open(base + ".csv", "w") as f:
        f.write("ra,dec,phot_g_mean_mag,bp_rp\n")
        for r in stars:
            f.write(f"{r[0]},{r[1]},{r[2]},{'' if r[3] is None else r[3]}\n")
    print("saved", base + ".csv")
