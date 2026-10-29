# Third-party notices

The root MIT license applies to CultureForge's original software. Dependencies, fonts, API data and third-party media retain their own terms.

| Component | Source / terms |
| --- | --- |
| Qloo cultural evidence and venue photographs | [Qloo](https://qloo.com/), accessed through the [official Hackathon Kit](https://github.com/qloo/qloo-hackathon-kit). API data and photographs are not relicensed under CultureForge's MIT license. The UI identifies Qloo evidence and image sources. Use remains subject to the account/API terms and any underlying rights. |
| Geist Pixel Circle | [Vercel Geist Pixel](https://github.com/vercel/geist-pixel-font), SIL Open Font License 1.1; the original notice is included in [fonts/OFL.txt](fonts/OFL.txt). |
| Inter, loaded through Google Fonts | [Inter project](https://github.com/rsms/inter), SIL Open Font License 1.1. |
| Font Awesome Free, loaded through cdnjs | [Font Awesome Free license](https://fontawesome.com/license/free): icons CC BY 4.0, fonts SIL OFL 1.1, code MIT. |
| fpdf2 (the PDF export) | [py-pdf/fpdf2](https://github.com/py-pdf/fpdf2), LGPL-3.0-or-later. Used unmodified as a library dependency installed from PyPI; it is not vendored or relicensed here. |
| React, Vite, Tailwind CSS, Motion, Lucide, FastAPI, Pydantic, Uvicorn | Respective upstream projects. Package license files remain with their distributions; consult installed packages and lockfiles for exact versions and terms. |

## Landing background

The landing page's background is drawn in code by `landing/landing-scene.js` (sine waves and a hash function). It contains no
video, photograph or other third-party media. An earlier version used a video downloaded from MotionSites AI, whose
terms state that the site owns its video backgrounds and do not permit republishing them; that video and its poster
image were removed.

## Owner review before publication

`assets/logo.webp` and the product screenshots in `docs/screenshots/` have no creation or purchase records in the
repository. Confirm ownership or suitable permissions for publication and redistribution. The software license does not
establish media ownership. Set `ownerConfirmedAssetRights` in submission.json only after this review.

The external Bubbledot font stylesheet has been removed; the landing page uses the bundled, licensed Geist Pixel Circle display font. Product screenshots should reflect the final build and must not be described as user/customer validation.

No affiliation, endorsement or sponsorship by any pictured venue is implied. A Qloo reference place illustrates retrieved cultural evidence, not a proposed business's existing location.
