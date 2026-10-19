# RE05 – Spooky Cereals: The Greys

## Summary

`re05.exe` is a .NET Framework executable that acts as a loader. It contains an encrypted inner .NET assembly (`dllBytes`) and decrypts it with an XOR key before loading it via reflection. The embedded key is intentionally wrong, so the first task is recovering the real XOR key. The inner assembly then asks for a password, checks its MD5 against a stored hash, and uses the password to AES-decrypt the flag.

**Flag:** `deadface{Before_Consenting_to_Med_Exam_Ascertain_Destination_of_Finger!}`

## Step 1: Inspect the outer loader

Running the binary prints a banner and then fails:

```
[!] Error: Not a valid assembly. Could not load file or assembly '6656 bytes loaded from Program...'
[!] Error: Vibe-Coded @#$!#%$& Detected!  Assembly is BORKED!
```

Reflection shows the loader class `DllLoader.Program` with two static fields:

- `dllBytes : byte[6656]`
- `xorKey : byte[2] = 01-01`

The IL for `Main` decrypts in place:

```csharp
for (int i = 0; i < dllBytes.Length; i++)
    dllBytes[i] ^= xorKey[i % xorKey.Length];

Assembly asm = Assembly.Load(dllBytes);
Type type = asm.GetType("MyNamespace.MyClass");
object instance = Activator.CreateInstance(type);
MethodInfo run = type.GetMethod("Run");
run.Invoke(instance, null);
```

The embedded key `[0x01, 0x01]` is the "bad key" mentioned in the error message.

## Step 2: Recover the real XOR key

A valid .NET PE assembly begins with the MZ header:

```
4D 5A 90 00 03 00 00 00 04 00 00 00 FF FF ...
```

The first ciphertext bytes are:

```
0C 69 D1 33 42 33 41 33 45 33 ...
```

XORing the first two bytes with `M` (`0x4D`) and `Z` (`0x5A`) gives:

```
0x0C ^ 0x4D = 0x41  ('A')
0x69 ^ 0x5A = 0x33  ('3')
```

Using key `[0x41, 0x33]` decrypts the entire 6656-byte payload into a valid assembly (`DLLPayload`).

## Step 3: Inspect the inner assembly

The inner assembly contains `MyNamespace.MyClass` with instance fields:

- `correctHash : byte[16]` = `77 30 E6 66 6B EC 3D C3 46 C1 05 BD 20 12 A8 13`
- `encryptedFlag : byte[80]`
- `iv : byte[16]` = ASCII `thegreysarecomin`

Relevant methods:

- `CalculateMD5Hash(string)` – returns MD5 bytes.
- `CompareByteArrays(byte[], byte[])` – compares two byte arrays.
- `DecryptAES(byte[] encryptedData, string password, byte[] iv)` – AES-256-CBC with PKCS7 padding. Key derived via `Rfc2898DeriveBytes(password, iv, 1000)` taking 32 bytes. The IV is also used as the PBKDF2 salt.
- `Run()` – prompts for a password, hashes it, compares to `correctHash`, and if correct decrypts `encryptedFlag` using `password + password`.

## Step 4: Crack the password

The target MD5 is:

```
7730e6666bec3dc346c105bd2012a813
```

This matches the MD5 of:

```
booberry
```

## Step 5: Decrypt the flag

`Run()` uses the AES password:

```
booberrybooberry
```

Deriving the key with PBKDF2-HMAC-SHA1 (1000 iterations, salt = IV, 32 bytes) and decrypting `encryptedFlag` with AES-256-CBC gives:

```
deadface{Before_Consenting_to_Med_Exam_Ascertain_Destination_of_Finger!}
```