# ImaginaryCTF 2025/misc-certificate

Writeup for the Challenge "certificate" misc category in ICTF 2025 playing with THEM?!

---

**Category:** misc

**Author:** Eth007

**Descritopn:** As a thank you for playing our CTF, we're giving out participation certificates! Each one comes with a custom flag, but I bet you can't get the flag belonging to Eth007!

**Flag Format:** ictf{\*}

---

## Challenge

We are given a certificate generator at:

```
https://eth007.me/cert/
```

The HTML/JS shows how the flag is created. Inside the script there is a function:

```js
function customHash(str){
  let h = 1337;
  for (let i=0;i<str.length;i++){
    h = (h * 31 + str.charCodeAt(i)) ^ (h >>> 7);
    h = h >>> 0;
  }
  return h.toString(16);
}

function makeFlag(name){
  const clean = name.trim() || "anon";
  const h = customHash(clean);
  return `ictf{${h}}`;
}
```

The SVG certificate stores the flag inside the `<desc>` tag.

However, if you type `Eth007` as the participant name, the code replaces it with `REDACTED`:

```js
if (name == "Eth007") {
    name = "REDACTED"
}
```

So we can’t just generate it directly from the site.

---

## Solution

We run the custom hash function locally with the input `"Eth007"`. That produces:

```
7b4b3965
```

So the final flag is:

```
ictf{7b4b3965}
```

---

## Flag

```
ictf{7b4b3965}
```

