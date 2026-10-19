# Chatty Cathy — DEADFACE CTF 2026 (OSINT / web, 15 pts)

> *@RP-01? — There is a DEADFACE member who writes a travel blog under the pseudonym
> "Alice". Can you check GhostTown and see if you can find the travel blog? We suspect the
> site may contain information needed to track down this DEADFACE member.*
>
> NOTE: the IP address is hosting other open ports for other challenges, only the website
> at 8443 is relevant to this challenge.
>
> Submit the flag as: `deadface{flag_text}`

**Flag:** `deadface{y0u_m3ddling_k!ds}`

```
deadface{y0u_m3ddling_k!ds}
```

---

## Solution overview

Two pieces, one chain:

| # | Piece | Where |
|---|-------|-------|
| 1 | **OSINT** — find the travel blog | GhostTown search → *Travel Destinations* (`/t/20/…`) → `lamia415` |
| 2 | **Web** — the hidden flag on the blog | `https://170.187.156.131:8443/robots.txt` |

There is a follow-up OSINT challenge that re-uses the same site (see [below](#follow-up-the-certificate)),
where the "information needed to track down this member" turns out to be the member's real
identity hidden in the site's TLS certificate.

---

## 1. Finding the blog

GhostTown (`https://ghosttown.deadface.io`) is the DEADFACE forum and the intended starting
point. Its search is a simple GET form (`/search?q=…`), so we search for the obvious keyword
**`travel`**:

```
GET https://ghosttown.deadface.io/search?q=travel
```

That returns the thread **Off-Grid → Travel Destinations**:

```
https://ghosttown.deadface.io/t/20/travel-destinations
```

The thread opens with `lamia415` ("anyone else find it impossible to fully unplug?") and then
drops the link:

> **lamia415:** *"i know, i know. old habits. the views were too good not to share, i put them
> all up on my little travel blog `https://170.187.156.131:8443/`"*

The rest of the thread is pure flavour but confirms the ident:

> **luciafer:** *"Are you sure you want to share that? It has your first name on it"*
> **lamia415:** *"nothing links back to me, first name is nothing"*
> **sunstalker:** *"…'nothing links back to me' is what everyone says right before it does"*

So the DEADFACE member is **`lamia415`**, and the "Alice" blog is at
`https://170.187.156.131:8443/`.

## 2. The blog and the flag

The site is a static "Wander with Alice" travel blog:

```
$ curl -sk https://170.187.156.131:8443/
```

```html
<h1>Wander with Alice</h1>
<div class="tag">chasing sunsets, one boarding pass at a time</div>
<p class="about">Hi, I'm Alice … I quit the desk job, kept the window seat. …
   I love the beach more than anything, it is my favorite vacation spot.
   I will keep posting these on both profiles in case this stops working</p>
```

Two posts: a "latest post" *My Favorite Little Restauraunt* (with an image —
`static/other1.png`, which is actually served at `/static/other.png` and shows a whitewashed
Cycladic street on a Greek island), and an older packing-light post.

The flag is stashed the classic way — `robots.txt`:

```
$ curl -sk https://170.187.156.131:8443/robots.txt
User-agent: *
Disallow: /secret_members
# deadface{y0u_m3ddling_k!ds}
```

> 🏁 **`deadface{y0u_m3ddling_k!ds}`** — "you meddling kids". 🙂

---

## Follow-up: the certificate

> *Now that you've found the DEADFACE member's travel blog, what else can we determine about
> this site and this member? Perhaps the site's certificate can tell us more.*

The site on `8443` is served over TLS with a **self-signed** certificate. Pulling it:

```bash
openssl s_client -connect 170.187.156.131:8443 </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -ext subjectAltName
```

(the same fields can be read on Windows with a `SslStream`, or in Python with
`ssl` + `cryptography`).

```
Subject: E=alicehankerty@gmail.com, CN=170.187.156.131, OU=Operations,
         O=Deadface{c@tch_m3_if_y0u_c@n}, L=New Orleans, S=Louisiana, C=US
Issuer : (same — self-signed)
SAN    : IP Address=170.187.156.131,
         DNS Name=deadface.ctf,
         RFC822 Name=alicehankerty@gmail.com
```

Two things fall out of this:

1. The **O (Organization)** field contains a flag-shaped string,
   `Deadface{c@tch_m3_if_y0u_c@n}` ("catch me if you can"). This is a **planted taunt/decoy**,
   not the flag.
2. The **email / SAN** field leaks the member's real identity behind `lamia415`:
   **`alicehankerty@gmail.com`** → **Alice Hankerty**.

So the intended answer to "what else can we determine about this site *and this member*" is the
member's **identity**, not the bait string.

> **Flag (follow-up):** `deadface{alice_hankerty}`

> Note: the exact encoding of the name is the only ambiguity here (e.g.
> `alice_hankerty` / `Alice_Hankerty` / `alicehankerty`); the value itself comes straight from
> the cert's `E=` / SAN fields. The `O=Deadface{c@tch_m3_if_y0u_c@n}` value is a
> deliberate decoy and is rejected by the platform.

### Confirming the identity link

The identity is corroborated by the site's own hidden login (the path disallowed in
`robots.txt`):

```
$ curl -sk https://170.187.156.131:8443/secret_members
```

A "Member Login" page. Supplying the cert's email local-part:

```
$ curl -sk -X POST https://170.187.156.131:8443/secret_members --data 'username=alicehankerty'
```

…returns *"Signing in as **alicehankerty**"* plus a password prompt and a **Show hint** button:

```
$ curl -sk -X POST https://170.187.156.131:8443/secret_members \
       --data 'username=alicehankerty&hint=1'
<div class="hint">What is your favorite vacation spot?</div>
```

i.e. the `robots.txt` username (`alicehankerty`) is exactly the cert's email local-part — the
cert **is** the bridge between the anonymous `lamia415` handle and the real person.

---

## Tools / quick repro

```bash
# 1. find the blog
curl -sk 'https://ghosttown.deadface.io/search?q=travel'

# 2. the flag
curl -sk https://170.187.156.131:8443/robots.txt

# 3. the certificate (identity + decoy)
openssl s_client -connect 170.187.156.131:8443 </dev/null 2>/dev/null \
  | openssl x509 -noout -text
```

Notes:
- The other open ports on `170.187.156.131` (80/301, 8080 *Grave Encounters*, 2049) belong to
  **other** challenges and are out of scope for this one.
- `static/other1.png` in the page source 404s; the real photo is `/static/other.png` (a Greek /
  Cycladic street — relevant if a follow-on asks "where did she end up").
