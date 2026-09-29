#!/usr/bin/env python3
"""Windowed feature extraction from a pcap.

Tiers:
  count      - deauth frames per window
  structural - distinct src addrs, address entropy, inter-arrival regularity
  semantic   - reason-code distribution, deauth-to-reassociation ratio
Labels each window from the ground-truth log.
"""

def main():
    # TODO: read pcap; window it; compute features; write labelled table.
    pass

if __name__ == "__main__":
    main()
