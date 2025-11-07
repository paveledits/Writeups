# V1t CTF 2025/OSINT-The Forgotten Inventory

Writeup for the Challenge "The Forgotten Inventory" OSINT category in V1t CTF 2025 playing  
with THEM?!

------------------------------------------------------------------------

**Category:** OSINT  
**Description:**  
> In the summer of 2007, a massive archive quietly surfaced - a meticulous ledger of items that once rolled across desert sands under foreign command. The file was structured, line after line, page after page, each entry tied to a unit whose banners flew far from home.
>
> Someone wasn’t happy about its release. A message was sent, demanding its silence - a digital plea from a uniformed gatekeeper. The request was denied.
>
> Your task is to uncover the sender of that plea.
>
> Clues hide in old public archives - look for a tabular trail documenting what was once called Operation Freedom, catalogued in a comma-separated vault of 1,996 pages worth of equipment.
>
> Some say the sands between two nations hold the real context - where east met west, and war turned into a spreadsheet.
>
> **Find the email address of the official who tried to bury the list.**
>
> Format: `v1t{hello.hi@whatever.com}`

**Flag Format:** v1t{*}

## Challenge

The challenge hinted at a leaked dataset from the Iraq War, describing a huge CSV file containing equipment inventories from *Operation Iraqi Freedom* (OIF). It mentioned 1,996 pages of entries and a government official trying to take the archive down. This clearly referenced an incident around **2007**, when U.S. military supply data was leaked online.

------------------------------------------------------------------------

## Step 1 --- Initial Analysis

The first clues pointed toward a CSV file and a takedown request about a military equipment list. Searching terms like:

```
Operation Freedom 1996 pages csv site:archive.org
"Iraq" "equipment" "FORSCOM" "csv"
```

brought up an old mirror of **Iraq OIF Property List.csv** hosted on data leak archives (and mentioned in Reddit / OSINT circles).

------------------------------------------------------------------------

## Step 2 --- Digging Deeper

Opening the archived metadata for that CSV on Archive.org revealed an attached notice under *takedown correspondence*. It contained a formal U.S. Army message titled:

> *"Request to remove sensitive file Iraq OIF Property List.csv"*

The sender was listed as:

> **CW2 David J. Hoskins (FORSCOM)**  
> **Email:** `david.j.hoskins@us.army.mil`

The message was essentially a digital plea to have the dataset removed due to sensitivity of internal logistics information, confirming he was the gatekeeper referenced in the challenge.

------------------------------------------------------------------------

## Step 3 --- Solution

After verifying the authenticity of the message and that the archive remained public, the final answer became clear:

```
v1t{david.j.hoskins@us.army.mil}
```

---

## Flag

```
v1t{david.j.hoskins@us.army.mil}
```

---

## Notes

This was a classic OSINT sleuth - starting from a narrative reference to a historical leak (Operation Iraqi Freedom logistics data), correlating the 1,996-page clue to the CSV dump, then locating the U.S. Army takedown request on public mirrors. It’s a nice callback to how transparency archives sometimes preserve even the takedown attempts themselves.

