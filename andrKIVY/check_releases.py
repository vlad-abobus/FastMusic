import json, sys, urllib.request
data = json.loads(urllib.request.urlopen("https://api.github.com/repos/T-Dynamos/materialyoucolor-python/releases").read())
for r in data[:8]:
    print(r["tag_name"])
