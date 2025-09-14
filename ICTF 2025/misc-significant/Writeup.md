# ICTF 2025/misc-significant

Writeup for the Challenge "significant" misc category in ICTF 2025 playing  
with THEM?!

------------------------------------------------------------------------

**Category:** misc

**Author:** Eth007

**Descritopn:** The signpost knows where it is at all times. It knows this because it knows where it isn't, by subtracting where it is, from where it isn't, or where it isn't, from where it is, whichever is greater. Consequently, the position where it is, is now the position that it wasn't, and it follows that the position where it was, is now the position that it isn't.

**Flag Format:** ictf{lat,long}

## Challenge

We are given an image `significant.jpg`. I embedded it here:

  
![significant](https://github.com/user-attachments/assets/515e0fc4-d82f-468b-ad14-e8a23bf86c01)


It shows a signpost with arrows pointing to world cities with exact mile distances.  
I need to find the coordinates of this signpost to three decimals.

------------------------------------------------------------------------

## Step 1 --- First thoughts

The sign had distances like:

- Sydney 7432 mi  
- Paris 5570 mi  
- Ho Chi Minh 7830 mi  
- Bangkok 8707 mi  

This looked like a **sister cities signpost**, a common landmark type in major cities.

------------------------------------------------------------------------

## Step 2 --- OSINT

Searching for *“sister cities sign Sydney 7432 Paris 5570”* led to a [blog post](https://www.sfmta.com/blog/sister-cities-sign-unveiled-hallidie-plaza) on the **San Francisco Municipal Transportation Agency** site.  
It confirmed that a Sister Cities sign was unveiled at **Hallidie Plaza**, right at the Powell Street cable car turnaround in San Francisco.

The distances in the blog matched exactly with the ones in the challenge image.

------------------------------------------------------------------------

## Step 3 --- Coordinates

Cross-checking Hallidie Plaza on maps gave:

- Hallidie Plaza GPS: **37.784632, -122.407939**  
- Rounded to 3 decimals: **37.785, -122.408**

------------------------------------------------------------------------

## Step 4 --- Result

The final flag is:

    ictf{37.785,-122.408}

------------------------------------------------------------------------

## Notes

This was a clean OSINT challenge and the distances served as a unique verifier.
