# Build an IPA from Windows

The **Build iOS IPA** GitHub Actions workflow runs on a hosted Apple Silicon Mac.
You do not need a Mac or an Apple developer account to build this sideloadable IPA.
The full build still requires your own game dumps: game code is linked into the app.

## One-time setup

1. Create a ZIP containing these three files at its root, with these exact names:
   `prod.keys`, `base.nsp`, and `upd4-0-1.nsp` (update 4.0.1).
   The base game may also be named `game.nsp` or `game`; the downloader renames
   it automatically. The update may also be named `update.nsp` or `update`.
   Include only one file for each input. Filename case is ignored.
2. Upload the ZIP to Google Drive, then open **Share → General access → Anyone with
   the link**, choose **Viewer**, and copy the file's link. Keep downloads enabled.
   The downloader handles Drive's large-file confirmation page. Store the link only
   in the secret below; anyone who obtains it can download the ZIP. After the build,
   you can switch the file back to **Restricted**. A direct HTTPS download URL from
   another host also works. Do not commit the ZIP or keys.
3. Open **Settings → Secrets and variables → Actions → New repository secret**.
   Add `MUSH8_INPUTS_URL` with the download URL. No password secret is required.
4. Open **Actions → Build iOS IPA → Run workflow**, choose `main`, and run it.
   If the fork's Actions page asks you to enable workflows, enable them first.

The first source-tools check runs when the workflow is added. Without the URL secret,
it compiles the host tools and reports that the IPA is waiting for your files.
It does not claim to have produced an IPA. Full builds may take 20–60 minutes or more.
They can still fail on toolchain, runner disk-space, or game-data issues.

## Download

After a successful full build, tell the build assistant the run is complete. It will
retrieve the **Mush8-IPA-transfer** artifact, decrypt it, and deliver the normal
`Mush8.ipa` privately. You do not need to create or enter a password.

The public artifact contains only `Mush8.ipa.cms`, encrypted automatically with the
public certificate in `tools/ipa-delivery-cert.pem`. The matching private delivery
key is retained separately in the build owner's files and is never committed or
sent to GitHub. The transfer artifact expires after one day. It cannot be installed
directly; the assistant must first decrypt it. Original dumps and build directories
are not uploaded as artifacts.

Install `Mush8.ipa` with AltStore or SideStore. It is ad-hoc signed for sideloading;
the installer signs it for your account. The project targets iOS 26 or later.
Copy your game files and dumped Firmware folder into the app as described in README.md.
Building an IPA does not verify that it works on a physical iPhone.

## A16 GPU heap compatibility

The renderer splits the guest heap into Metal buffers no larger than the device's
maxBufferLength. Buffer bindings that cross a segment boundary use staging, and
shader global-memory accesses resolve the correct segment. This addresses the
reported failure to wrap the roughly 3 GiB guest heap on A16; device testing is
still required to confirm the black-screen symptom is resolved.

The segmentation changes and boundary tests are adapted from lyccccy's
[c22dev/mush8 PR #3](https://github.com/c22dev/mush8/pull/3),
commit 9080fa00080bf1b74ecf44ac4729cf17827bda6f. Unrelated changes are excluded.
The iOS packager and verifier use the same heap-segments-v2 shader directory as
the renderer, ensuring old shader libraries with the previous ABI are not used.
