# Publish this preview to GitHub

The connected GitHub account previously used for PDF Studio Pro is `IRFANSK-him`.

1. Go to https://github.com/new?name=PDF-Studio-Pro-v1.0-release-preview
2. Set owner to `IRFANSK-him`.
3. Set the repository name to `PDF-Studio-Pro-v1.0-release-preview` (GitHub does not retain spaces in repository URL names).
4. Choose **Private** while testing, and leave **Initialize with README**, **.gitignore**, and **license** unchecked (this local source already includes a README and gitignore).
5. Select **Create repository**.
6. Extract the project ZIP into a folder, open PowerShell or Git Bash in that folder and run:

```bash
git init -b main
git add .
git commit -m "Prepare PDF Studio Pro v1.0 release preview"
git remote add origin https://github.com/IRFANSK-him/PDF-Studio-Pro-v1.0-release-preview.git
git push -u origin main
```

This project archive contains no `.git` directory so these commands are safe to run in the extracted project folder. GitHub authentication may be required at push time. Do not upload the locally generated `secrets/` directory or any administrator token. The expected address is https://github.com/IRFANSK-him/PDF-Studio-Pro-v1.0-release-preview once you create it.
