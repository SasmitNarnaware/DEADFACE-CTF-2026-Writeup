# DEADFACE CTF Write-up — Travel Destinations

**Category:** Web / OSINT  
**Platform:** DEADFACE GhostTown  
**Objective:** Find the travel blog written by a DEADFACE member using the pseudonym “Alice” and recover the flag.

## 1. Starting Point — GhostTown

I started by visiting the DEADFACE GhostTown forum:

https://ghosttown.deadface.io/

The challenge description mentioned a DEADFACE member who writes a travel blog under the pseudonym “Alice.” The goal was to find the blog and investigate the website for information that could help identify the member.

## 2. Forum Investigation

I opened the following GhostTown discussion:

https://ghosttown.deadface.io/t/20/travel-destinations

The thread contained clues about the travel blog and pointed me toward the target website.

## 3. Discovering the Target Website

From the discussion, I identified the website hosted at:

https://170.187.156.131:8443/

The challenge specifically stated that port **8443** was relevant, so I focused my investigation on this web service.

## 4. Enumerating `robots.txt`

To look for additional information exposed by the website, I checked its `robots.txt` file:

https://170.187.156.131:8443/robots.txt

The file contained the challenge flag.

## 5. Flag

```text
deadface{y0u_m3ddling_k!ds}
```

## 6. Key Takeaways

- Forum discussions can contain clues that lead to external websites.
- `robots.txt` is a useful first check during web reconnaissance.
- Although `robots.txt` is intended to provide crawling instructions, it is publicly accessible and can inadvertently reveal sensitive paths or challenge information.
- Follow the challenge's scope and focus on the explicitly relevant service.

## Conclusion

I started with the DEADFACE GhostTown forum, investigated the *Travel Destinations* discussion, identified the target website on port 8443, and retrieved the flag from its `robots.txt` file.

**Status:** Flag found.
