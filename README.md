# TUTTO

Master BibTeX bibliography (`tutto.bib`) shared across all writing projects.

This repo is the single source of truth for the bibliography. Individual
project repos (including ones synced with Overleaf, which doesn't support
git submodules or symlinks) each keep their own plain-file copy of
`tutto.bib`, updated from here by hand.

## Updating a project's copy

From this repo:

```
./sync-tutto-bib.sh /path/to/other/project
```

This fetches the latest `tutto.bib` from `origin/main` and copies it into
the target directory. Then commit the change in that project's own repo
as usual.

## Updating this repo with a newer bibliography

If you've been editing `tutto.bib` in a project instead of here, copy it
back:

```
cp /path/to/project/tutto.bib tutto.bib
git add tutto.bib
git commit -m "Update bibliography"
git push
```
