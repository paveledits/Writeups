# V1t CTF 2025/misc-Blank

Writeup for the Challenge "Blank" misc category in V1t CTF 2025 playing  
with THEM?!


------------------------------------------------------------------------

**Category:** misc
**Description:** This image is blank is it ?
**Flag Format:** v1t{*}

## Challenge

We are given only an image called "white.png" as a download.

------------------------------------------------------------------------

## Step 1 --- Initial Analysis

At first glance it looks like a white image, but because of the description I assumed the image would have something hidden inside the image itself, not in the binary of the image.

------------------------------------------------------------------------

## Step 2 --- Digging Deeper

So i opened up the image in Photoshop and played a around with it.

------------------------------------------------------------------------

## Step 3 --- Exploit / Solution

After a little bit of playing around i found out that if you lower the brightness and the contrast all the way you can see following:

<img width="1260" height="434" alt="Screenshot 2025-11-07 at 3 56 25 PM" src="https://github.com/user-attachments/assets/2cbe485e-f64f-4f5f-a0e1-a067900a27cc" />

---

## Flag

```
v1t{wh1t3_3y3s}
```
