# Přesun repozitáře z GitLabu na GitHub

Repozitář na GitLabu má jedinou větev `main` a žádné tagy, takže na přenos
celé historie stačí obyčejný push z pracovní kopie – mirror není potřeba.
Pracovní kopie obsahuje celou historii z GitLabu (43 commitů) a nové commity
ve větvi `revize-2026-10`.

Spusť u sebe v `C:\work-AI\tnk\extrakty\tnk136-extrakty`. Z Cowork sezení se
na GitLab ani GitHub nedostanu a nemám tvoje přihlašovací údaje.

## 1. Zkontrolovat a sloučit nové commity

```bash
git log --oneline main..revize-2026-10
git checkout main
git merge --ff-only revize-2026-10
```

## 2. Založit prázdný repozitář na GitHubu

Na <https://github.com/new>: název `tnk136-extrakty`, viditelnost podle uvážení,
**nezaškrtávat** README, .gitignore ani licenci.

## 3. Přepnout původ a nahrát

```bash
git remote rename origin gitlab
git remote add origin https://github.com/<uzivatel>/tnk136-extrakty.git
git push -u origin main
```

GitLab tím zůstane jako záložní vzdálený repozitář `gitlab`. Když ho už
nechceš, `git remote remove gitlab`.

## 4. Zapnout zápis pro GitHub Actions

Workflow `.github/workflows/docx2md.yml` commituje vygenerovaný Markdown zpět
do větve. Aby mohl pushovat:

**Settings → Actions → General → Workflow permissions → Read and write permissions**

## 5. Co po přesunu zkontrolovat

- na GitHubu je stejný počet commitů jako lokálně (`git rev-list --count main`)
- v záložce Actions je workflow „Převod extraktů do Markdownu“; první běh se
  spustí až při změně Wordu v `extrakty/doc/` nebo ručně (Run workflow)
- odkazy v `index.md` vedou na existující soubory a obrázky v Markdownu se zobrazují

## Konce řádků

Pracovní kopie je na Windows s `core.autocrlf=true`; v repozitáři jsou texty
s LF. Commity z Cowork sezení se dělaly se stejným nastavením, takže v historii
nejsou změny jen v koncích řádků.
