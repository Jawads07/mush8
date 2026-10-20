# Build an IPA from Windows

The **Build iOS IPA** GitHub Actions workflow runs on a hosted Apple Silicon Mac.
You do not need a Mac or an Apple developer account to build this sideloadable IPA.
The full build still requires your own game dumps: game code is linked into the app.

## One-time setup

1. Create a ZIP containing these three files at its root, with these exact names:
   `prod.keys`, `base.nsp`, and `upd4-0-1.nsp` (update 4.0.1).
2. Upload the ZIP to Google Drive, then open **Share → General access → Anyone with
   the link**, choose **Viewer**, and copy the file's link. Keep downloads enabled.
   The downloader handles Drive's large-file confirmation page. Store the link only
   in the secret below; anyone who obtains it can download the ZIP. After the build,
   you can switch the file back to **Restricted**. A direct HTTPS download URL from
   another host also works. Do not commit the ZIP or keys.
3. Open **Settings → Secrets and variables → Actions → New repository secret**.
   Add `MUSH8_INPUTS_URL` with the download URL, and `MUSH8_IPA_PASSWORD` with a strong,
   unique password. Keep the password: it is needed to decrypt the result.
4. Open **Actions → Build iOS IPA → Run workflow**, choose `main`, and run it.
   If the fork's Actions page asks you to enable workflows, enable them first.

The first source-tools check runs when the workflow is added. Without both secrets,
it compiles the host tools and reports that the IPA is waiting for your files.
It does not claim to have produced an IPA. Full builds may take 20–60 minutes or more.
They can still fail on toolchain, runner disk-space, or game-data issues.

## Download and decrypt

After a successful full build, download the **Mush8-IPA-encrypted** artifact from the
run page and unzip it. Only an encrypted IPA is uploaded, since this is a public
repository and the IPA embeds game code. No dumps or build directories are uploaded.
The encrypted artifact expires after one day.

On Windows, open Git Bash in the folder containing `Mush8.ipa.enc` and run:

```bash
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 \
  -in Mush8.ipa.enc -out Mush8.ipa
```

Enter the password you saved in `MUSH8_IPA_PASSWORD`. The password is requested
interactively, so it does not appear in shell history.

Install `Mush8.ipa` with AltStore or SideStore. It is ad-hoc signed for sideloading;
the installer signs it for your account. The project targets iOS 26 or later.
Copy your game files and dumped Firmware folder into the app as described in README.md.
Building an IPA does not verify that it works on a physical iPhone.
