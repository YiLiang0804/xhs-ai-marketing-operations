# Public release privacy scope

[Back to the project overview](README.md)

## Identity and record-level information

This portfolio uses a generic organization description. It omits the studio's name, location, institutional associations, branding, staff identities and social-account references. The author's portfolio attribution is intentionally public; no personal or colleague XHS account is linked.

Mentor and lead rows are entirely synthetic. No original mentor names, aliases, internal keys, institutions, education histories, publications, narrow research combinations, client messages, post text, usernames, platform identifiers, URLs or contact details are included. Public synthetic IDs do not map back to original records.

## Aggregate information retained

Historical aggregate record counts are retained to communicate operating scale. Exact operating dates are withheld, and small run-status categories are grouped. Counts and broad business context can still be correlated with information someone obtains elsewhere; this does not guarantee that the organization cannot be inferred.

## Packaging and future releases

The release builder uses an explicit file allowlist. It does not recursively package the working directory. It excludes original workbooks, source archives, private materials, browser sessions, screenshots, runtime ledgers, bytecode, logs and Git history. ZIP entries use fixed timestamps, neutral attributes and empty metadata fields.

Before a future release, inspect changed content as well as filenames. Ignore rules and allowlists do not sanitize a secret pasted into an approved document. A previously published Git commit would require a separate history review; the local release builder does not examine remote repositories or prove that remote history is clean.

From the repository root, build the public archive outside the project directory:

```bash
python scripts/build_release.py --out ../output/public-release.zip
```
