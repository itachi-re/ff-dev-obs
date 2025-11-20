# Firefox Developer Edition – Version Tracker for OBS

This repository exposes a single file called `version` containing the latest
Firefox Developer Edition version string (e.g., `147.0b1`).

An automated GitHub Action checks Mozilla’s official version metadata every
6 hours:

https://product-details.mozilla.org/1.0/firefox_versions.json

It extracts:

