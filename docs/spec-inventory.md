# MediaWG Spec Inventory — Co-Chair Situational Awareness

Full status of all specs the dashboard tracks, for setting priority and spotting problems. Companion to `docs/spec-process-flow.md` and the co-chair study guide (`~/firefox-bug-investigation/media-wg/co-chair-prep.md`).

**Compiled:** 2026-07-13 · one research pass per spec. Treat exact WPT percentages and issue numbers as point-in-time — verify live before quoting. WPT dashboards are JS-rendered; some per-browser numbers are approximate.

---

## Executive summary

**Recurring pattern across the group:** most specs are **shipped in browsers for years but still sit at WD**, and the common blocker to CR is not design — it's **(a) unresolved horizontal-review debt, (b) single-vendor implementation, and (c) thin/absent WPT coverage** for newer surface. The charter's 2026–2027 REC dates are aggressive against this reality.

**Two governance decisions a co-chair should force early:**
1. **Media Playback Quality** — ED-only, shipped everywhere; charter says fold into HTML. Decide: push to FPWD→REC, or park as Note / upstream to WHATWG HTML. (Issue #28.)
2. **Document Picture-in-Picture** — already shipping (Firefox 151) but incubated in **WICG, not MediaWG**. Decide whether/when to bring it onto the MediaWG track.

**Coverage note:** the charter also lists **DataCue** + **6 registries** (codec ID, byte-stream, init-data formats) as deliverables that this dashboard does **not** track. Media Playback Quality is a charter *Note* (fold into HTML), not one of the 8 normative deliverables — a mismatch to reconcile in the dashboard.

**Editor bus-factor flag:** I (Alastor Wu / Mozilla) am editor of **autoplay** and co-editor of **audio-session** — both are single-vendor and low-velocity. Chairing those with a conflict-of-interest hat off matters.

## Priority matrix

| Tier | Spec | Stage | Charter CR / REC | Headline problem | Why this tier |
|---|---|---|---|---|---|
| **1 — flagship, critical path** | WebCodecs | WD (8 Jul'26) | CR Q1'26 *(slipped)* / REC Q4'26 | CR-blockers open (audio priming #626, colorspace #940); no EME story; huge surface | Highest activity + widest cross-WG deps; REC date at risk |
| **1** | Media Capabilities | WD (9 Jun'26) | CR Q4'25 *(missed)* / REC Q4'26 | Fingerprinting posture; HDR↔codec mapping unsettled; scope creep | CR target already passed; needs privacy signoff + V1 scoping |
| **1** | Media Source Extensions | WD (4 Nov'25) | CR Q4'26 / REC Q2'27 | Vendor-split extensions (MMS Safari-only, Workers Firefox-missing); core append interop bugs | Foundational streaming spec; interop risk is structural |
| **1** | Encrypted Media Extensions 2 | WD (7 Jul'26) | CR Q4'26 / REC Q2'27 | Interop fragmentation (no CDM spec); key rotation #132 (~9y open); DRM politics | High stakes + politically sensitive; maintenance bandwidth question |
| **2 — active, advancing** | Picture-in-Picture | WD (16 Jun'26) | CR Q2'26 / REC Q1'27 | CR-blocker #261 (activation consumption); Document-PiP scope question | Close to CR; resolve blocker + governance call |
| **2** | Media Session | WD (5 Jun'26) | CR Q4'26 / REC Q2'27 | Interop drift on new actions; Firefox laggard (68% WPT); action governance | Shipped core, but expanding surface needs an extensibility story |
| **3 — needs a decision** | Autoplay Policy Detection | WD (4 Sep'25) | CR Q2'26 / REC Q2'27 | **Firefox-only**; open privacy/security/a11y review debt; stalled | Single-vendor → CR is unrealistic without Chrome/Safari commitment |
| **3** | Audio Session | FPWD (7 Nov'24) | CR Q4'26 / REC Q2'27 | **Safari-only**; near-dormant; CR-blocker capture/type behavior (#46/#3) | Single-vendor + low velocity vs an open CR push |
| **3** | Media Playback Quality | **ED only** | — (charter Note) | Fold-into-HTML vs standalone unresolved (#28); Chrome-only WPT | Least mature; decide park/upstream vs formalize |

---

# Spec details

## Audio Session (`audio-session`)
- **Stage / repo / TR:** First Public Working Draft (7 Nov 2024), on Rec track, actively preparing for Candidate Recommendation · w3c/audio-session · [TR](https://www.w3.org/TR/audio-session/) (ED: https://w3c.github.io/audio-session/). Editors: Youenn Fablet (Apple), Alastor Wu (Mozilla).
- **One-liner:** Lets a web page declare the *type* of audio it produces so the platform can decide how that audio coexists with other apps/tabs (pause, duck, mix, or play exclusively).
- **Brief:** Solves the gap where web media can't integrate with OS-level audio focus/mixing the way native apps do. Core surface: `navigator.audioSession` → `AudioSession` (EventTarget) with a writable `type` (`AudioSessionType`: `auto`, `playback`, `transient`, `transient-solo`, `ambient`, `play-and-record`), a read-only `state` (`active`/`interrupted`/`inactive`), and `onstatechange`. `transient-solo` is exclusive; `play-and-record` gates microphone/capture.
- **Direction / roadmap:** Moving from FPWD toward CR — issue [#44](https://github.com/w3c/audio-session/issues/44) tracks CR-blocking work and horizontal reviews (accessibility self-review done [#42](https://github.com/w3c/audio-session/issues/42); APA review pending). v-next: per-element/per-AudioContext linking ([#5](https://github.com/w3c/audio-session/issues/5)), a `ducked` state ([#11](https://github.com/w3c/audio-session/issues/11)), output-route/sinkId selection ([#6](https://github.com/w3c/audio-session/issues/6)). Repo activity low — last substantive commits early-to-mid 2025.
- **Hot discussions (top 3-5):**
  - [#46](https://github.com/w3c/audio-session/issues/46) — Real-world misuse: sites set `type=playback`, so WebKit throws `InvalidStateError` on `getUserMedia`; debate on making the API more forgiving vs. auto-switching type.
  - [#3](https://github.com/w3c/audio-session/issues/3) — When an explicit session is set, should incompatible APIs like `getUserMedia` fail, auto-switch, or activate a different session? Core interop question.
  - [#5](https://github.com/w3c/audio-session/issues/5) — Bind a session per `HTMLMediaElement`/`AudioContext` rather than one per-document.
  - [#6](https://github.com/w3c/audio-session/issues/6) — Should the session specify output speaker/route options (sinkId-style).
  - [#4](https://github.com/w3c/audio-session/issues/4) — Scope and defaulting rules (foundational, still open).
- **Pushback / risks / problems:** No formal vendor objection, but the central unresolved tension is error/compatibility behavior between session type and capture APIs ([#46](https://github.com/w3c/audio-session/issues/46), [#3](https://github.com/w3c/audio-session/issues/3)) — a spec-vs-reality mismatch already breaking sites in Safari. Desktop audio-focus enforcement is under-specified/optional ([#12](https://github.com/w3c/audio-session/issues/12)). Two-engine interop is the biggest risk: only Safari has a real implementation.
- **WPT status:** Small suite — 3 test files, ~40 subtests. Aligned experimental run: Safari ~35/40 (~88%, functional), Chrome 14/40 (~35%), Firefox 14/40 (~35%). Chrome/Firefox pass only partial IDL subtests and 0 functional → effectively no implementation. Thin (no interruption/state-change or capture-interaction tests).
- **Browser support:** Safari shipped (`AudioSession`/`.type` in Safari 16.4+, iOS mirror). Chrome: not shipped (a related "AudioContext Interrupted State" intent exists on blink-dev). Firefox: not shipped despite a Mozilla editor; no public intent found. MDN: "Limited availability / Experimental."
- **Co-chair attention flags:** Single-engine reality (Safari-only) — watch for Chrome/Firefox intents before pushing CR ([#44](https://github.com/w3c/audio-session/issues/44)). Capture/type-compatibility behavior ([#46](https://github.com/w3c/audio-session/issues/46), [#3](https://github.com/w3c/audio-session/issues/3)) is a CR blocker breaking real sites. Low repo velocity vs an open CR push — confirm progress vs stall. APA a11y review still pending. WPT suite too thin to gate interop. Firefox is co-editor (me) but has no ship signal — internal priority call needed.

## Autoplay Policy Detection (`autoplay`)
- **Stage / repo / TR:** W3C Working Draft (latest 2025-09-04, Media WG) · w3c/autoplay · [TR](https://www.w3.org/TR/autoplay-detection/) (ED: https://w3c.github.io/autoplay/). Editor: Alastor Wu (Mozilla).
- **One-liner:** Adds `Navigator.getAutoplayPolicy()` so pages can detect whether media/audio autoplay is `allowed`, `allowed-muted`, or `disallowed` before attempting playback.
- **Brief:** `getAutoplayPolicy()` with an `AutoplayPolicy` enum and `AutoplayPolicyMediaType` (`mediaelement`/`audiocontext`); callable by media type, a specific `HTMLMediaElement`, or an `AudioContext`. Scope deliberately limited to HTML media + Web Audio (Web Speech and GIFs excluded). Originated from Firefox's autoplay work. Spec warns the policy can change over time → sites should re-query.
- **Direction / roadmap:** Largely maintenance, not active feature dev. Design churn ended ~2023–2024; 2025 commits were housekeeping. Only fresh 2026 activity is a batch of security/privacy-review issues (#47–#49, Mar 2026). No CR push signal.
- **Hot discussions (top 3-5):**
  - [#48](https://github.com/w3c/autoplay/issues/48) — spec teaches a detect-and-circumvent pattern (swap audible for muted to keep playing); proposal to make "pause on becoming audible without activation" normative (from security review).
  - #42 / #43 — privacy: fingerprinting/XS-leak risk; both tagged `privacy-needs-resolution`, open since Feb 2023.
  - [#47](https://github.com/w3c/autoplay/issues/47) — private-browsing-mode detection vector (Mar 2026).
  - [#44](https://github.com/w3c/autoplay/issues/44) — do we still need by-element/by-type overloads?
  - #25 / #36 — API only exposes current status-quo policy; "query by media type" shape feels inconsistent.
- **Pushback / risks / problems:** ~14 open issues, several unresolved from horizontal review — fingerprinting, private-browsing detection, circumvention-pattern / WCAG-1.4.2 (a11y). Bigger risk is adoption: **neither Chrome nor Safari has implemented it** despite "positive" positions — effectively single-vendor.
- **WPT status:** 3 test files (~22 subtests). Chrome ~14/22 (passes most `idlharness`, 0 on the two functional tests — consistent with not implementing the method). Firefox should pass functional tests (it ships the API) but exact per-browser numbers weren't retrievable; Safari has no meaningful passes.
- **Browser support:** **Firefox only.** Shipped Firefox 112 (2023), enabled by default (bug 1812189), incl. Android. Chrome/Edge: not shipped (~3.3% global usage, all Firefox). Safari: not shipped. MDN: Experimental.
- **Co-chair attention flags:** Single-vendor reality vs "positive" positions — Chrome & Safari signaled support but neither shipped after 3+ years; the headline Rec-track risk. Open horizontal-review debt (privacy/security/a11y) should close before advancing. Momentum stalled (editorial/review-driven only) — confirm a champion/plan for multi-vendor implementation or accept it stays a WD. Editor bandwidth (me) worth confirming.

## Encrypted Media Extensions (`encrypted-media`)
- **Stage / repo / TR:** W3C **Working Draft** (latest 7 Jul 2026) of EME **v2** (`encrypted-media-2`); **v1 is a REC, 18 Sept 2017** · w3c/encrypted-media · [TR](https://www.w3.org/TR/encrypted-media-2/) (ED: https://w3c.github.io/encrypted-media/).
- **One-liner:** JS API extending `HTMLMediaElement` to control playback of DRM-encrypted media by brokering license/key exchange between the page and a Content Decryption Module (CDM).
- **Brief:** Deliberately DRM-agnostic: page uses `requestMediaKeySystemAccess()` to negotiate a key system (Widevine, PlayReady, FairPlay, or interoperable Clear Key), creates `MediaKeySession`s, and shuttles opaque license messages to/from the CDM. EME specifies no decryption/DRM scheme (that's the black-box CDM). The absence of a mandated CDM spec is the root of most cross-vendor interop gaps.
- **Direction / roadmap:** v2 is largely maintenance + incremental over the 2017 REC. Additions: `encryptionScheme` capability (cenc/cbcs); `getStatusForPolicy()` for HDCP queries; Permissions-Policy `encrypted-media`; `usable-in-future` key status; (new 2026) `MediaKeySession.closed` promise + `MediaKeySessionClosedReason` (app close / internal error / **hardware context reset**), plus `QuotaExceededError`. 2026 editorial work targets conformance classes.
- **Hot discussions (top 3-5):**
  - [#132](https://github.com/w3c/encrypted-media/issues/132) (~76 comments, active May 2026) — continuous **key rotation** per MPEG CENC (ISO/IEC 23001-7); long-running, unresolved.
  - [#251](https://github.com/w3c/encrypted-media/issues/251) (Nov 2025) — specifying **mixed encrypted/unencrypted content**.
  - #494 / hardware context reset — session behavior on CDM state loss (drove the 2026 `closed`-reason work).
  - [#564](https://github.com/w3c/encrypted-media/issues/564) (Dec 2024) — proposed **Screen Capture Protection API** in EME config.
  - #166 / #192 — perennial: EME lacks a CDM spec and does too little to ensure CDM-level interop.
- **Pushback / risks / problems:** W3C's most politically contested spec. Its 2017 advancement drew a **Formal Objection** and **EFF's resignation** over standardizing DRM, anti-circumvention/DMCA exposure for researchers, and no covenant protecting them. Ongoing: **privacy** (distinctive identifiers, fingerprinting), **robustness/HDCP** gating, and **fragmentation** — because the CDM is unspecified, real interop between Widevine/PlayReady/FairPlay is effectively nil. Skews to slow maintenance vs abandonment; no formal at-risk list.
- **WPT status:** ~99 test files. Stable (~12 Jul 2026): Chrome ~97% (343/353), Edge ~96%, Firefox ~81% (277/341), Safari ~68% (194/285). **Caveat:** WPT CI can only exercise **Clear Key** — proprietary CDMs aren't testable cross-vendor, so numbers measure Clear Key + API surface, **not** DRM interop.
- **Browser support:** ~96% global. Universally shipped, but value is the key system, which fragments: Chrome→Widevine, Edge→PlayReady(+Widevine), Firefox→Widevine (Google-licensed CDM download), Safari→FairPlay. Clear Key is the only interoperable key system.
- **Co-chair attention flags:** Interop fragmentation — "supported everywhere" hides content-portability gaps. Privacy reviews for any new identifier/capability (screen-capture #564, HDCP queries). Maintenance-vs-abandonment: is there editor/implementer bandwidth for the 2026 cleanup + long-tail (#132, ~9y open)? Residual DRM-ethics sensitivity whenever advancing.

## Media Capabilities (`media-capabilities`)
- **Stage / repo / TR:** W3C Working Draft (latest 9 June 2026) · w3c/media-capabilities · [TR](https://www.w3.org/TR/media-capabilities/) (ED: https://w3c.github.io/media-capabilities/). Still WD despite years of shipping.
- **One-liner:** `navigator.mediaCapabilities.decodingInfo()` / `encodingInfo()` query whether a media config (codec, profile, resolution, bitrate, framerate, HDR) is *supported*, and predict *smooth* and *powerEfficient*.
- **Brief:** Supersedes boolean `isTypeSupported`/`canPlayType` with a promise-based `{supported, smooth, powerEfficient}`. Covers 3 decode surfaces (`file`, `media-source`, `webrtc`) + 2 encode (`record`, `webrtc`). Includes HDR signalling (colorGamut, transferFunction, ST 2086 / 2094-10 / 2094-40) and EME `keySystemConfiguration` queries.
- **Direction / roadmap:** Active: (1) **HDR** — capability↔codec-string mapping ([#245](https://github.com/w3c/media-capabilities/issues/245)), HDR-metadata registry ([#242](https://github.com/w3c/media-capabilities/issues/242)), SL-HDR ([#241](https://github.com/w3c/media-capabilities/issues/241)); (2) **WebRTC** — single-codec restriction ([#238](https://github.com/w3c/media-capabilities/issues/238)), `scalabilityMode`/SVC ([#159](https://github.com/w3c/media-capabilities/issues/159)); (3) **concurrent decode** ([#258](https://github.com/w3c/media-capabilities/issues/258)); (4) stereoscopic/immersive ([#249](https://github.com/w3c/media-capabilities/issues/249)).
- **Hot discussions (top 3-5):**
  - [#258](https://github.com/w3c/media-capabilities/issues/258) — concurrent playback: `maxConcurrent` vs a new `concurrentDecodingInfo()` (multiview/sports, DRM secure-memory limits).
  - [#245](https://github.com/w3c/media-capabilities/issues/245) / [#256](https://github.com/w3c/media-capabilities/issues/256) — colorGamut/transferFunction validation against codec-string color metadata.
  - [#238](https://github.com/w3c/media-capabilities/issues/238) / [#235](https://github.com/w3c/media-capabilities/issues/235) — do WebRTC configs keep the "exactly one codec" restriction.
  - [#242](https://github.com/w3c/media-capabilities/issues/242) / [#241](https://github.com/w3c/media-capabilities/issues/241) — HDR metadata registry + SL-HDR.
  - [#209](https://github.com/w3c/media-capabilities/issues/209) — PING privacy review re `scalabilityMode`/hardware-capability exposure.
- **Pushback / risks / problems:** **Fingerprinting** is the core tension — precise per-device smooth/powerEfficient + HDR + hw-decode answers are strong entropy (recurring PING concern [#209](https://github.com/w3c/media-capabilities/issues/209)). **Interop of predictions** — `smooth`/`powerEfficient` are heuristics; implementations diverge and Safari historically returns coarse/less-reliable values. At-risk normative gaps: channel-format definition, single-codec listing rule, WebRTC-applicability validation.
- **WPT status:** 12 test files (small). Latest stable: Chrome 286/332 (~86%), Firefox 279/321 (~87%), Safari 270/323 (~84%). Coverage thin vs the API surface (little on prediction quality, HDR permutations, WebRTC configs).
- **Browser support:** Baseline "widely available." `decodingInfo()`: Chrome 66, Firefox 63, Safari 13. `encodingInfo()`: Chrome 101 (much later), Firefox 63, Safari 15.4. Safari's decode predictions are the known weak spot for cross-browser reliability.
- **Co-chair attention flags:** Shipped everywhere but still WD — watch for a CR push; at-risk items (channel format, single-codec, WebRTC applicability) need resolution first. Privacy/fingerprinting ([#209](https://github.com/w3c/media-capabilities/issues/209)) needs clean PING/TAG signoff before advancing. Scope creep (concurrent decode #258, stereoscopic #249, deeper WebRTC/SVC) — decide V1 vs later. HDR↔codec mapping is the most substantive unsettled normative risk.

## Media Playback Quality (`media-playback-quality`)
- **Stage / repo / TR:** ED only (no /TR/) · [w3c/media-playback-quality](https://github.com/w3c/media-playback-quality) · —
- **One-liner:** Defines `HTMLVideoElement.getVideoPlaybackQuality()` returning `VideoPlaybackQuality` — `totalVideoFrames`, `droppedVideoFrames`, `corruptedVideoFrames` (deprecated), `creationTime`. ([ED](https://w3c.github.io/media-playback-quality/))
- **Brief:** Lets pages measure decode/render frame loss to adapt quality. Per the ED, "extracted from the [media-source] specification … to work on the playback quality problematic in a larger scope" — the counters originally lived in MSE (and historically HTMLMediaElement) and were split out so metrics apply to all `<video>`, not just MSE. A thin single-interface spec.
- **Direction / roadmap:** Dormant 2019–2024, then editor activity (@cynthia) Nov–Dec 2025; repo last pushed May 2026. **No FPWD ever published.** Live question (issue #28, Nov 2025): clean up and drive to REC vs upstream into HTML — noting "Every major browser is already shipping this feature." No decision recorded; that fork blocks a publication path.
- **Hot discussions (top 3-5):**
  - [#28](https://github.com/w3c/media-playback-quality/issues/28) — Proceed to REC vs upstream to HTML (roadmap-defining).
  - [#27](https://github.com/w3c/media-playback-quality/issues/27) — Remove deprecated `corruptedVideoFrames`.
  - #25 / #26 — new counters: harmonic framerate / reproduction jitter.
  - #32 — integrate with the media element load algorithm; #23 — clarify when `droppedVideoFrames` are expected; #13/#16/#17 — HTML integration (open since 2019).
- **Pushback / risks / problems:** No /TR/ because the group never resolved whether it justifies its own REC track or should fold into HTML (#28) — a one-method surface. Long inactivity (2019→2024 gap), ~15–19 open issues (several stale). Scope-creep risk (new counters) vs deprecating old. Already shipped everywhere → weak urgency to formalize.
- **WPT status:** Minimal — essentially one test, `idlharness.window.html` (~30 subtests). Chrome 30/30; Firefox/Safari/Edge show no recorded results (0/0). Only IDL-shape testing, no behavioral frame-drop tests, no cross-engine data.
- **Browser support:** Baseline "widely available" since Feb 2020. Firefox 42+, Safari 8+ (first), Chrome/Edge 80+. Good interop on the two core counters; `corruptedVideoFrames` inconsistent/deprecated.
- **Co-chair attention flags:** Least-mature spec — ED-only, tiny, already implemented everywhere. The chair decision is the #28 fork: push to FPWD→REC to formalize, or park as Note / upstream to HTML. Given it was carved out of MSE, upstreaming is credible. Before any REC push, WPT must move beyond a single Chrome-only IDL test; #27 (drop `corruptedVideoFrames`) should land first. Watch whether the Nov 2025 revival sustains.

## Media Session (`mediasession`)
- **Stage / repo / TR:** W3C Working Draft (5 June 2026) · w3c/mediasession · [TR](https://www.w3.org/TR/mediasession/).
- **One-liner:** Lets pages supply media metadata (title/artist/artwork) and register handlers for media-control actions so the OS/browser can drive playback from lock screens, notifications, media keys, and headset controls.
- **Brief:** `navigator.mediaSession` with `metadata`, `playbackState`, `setActionHandler()`, `setPositionState()`. Expanded beyond audio into video-conferencing controls (mic/camera/screenshare/hangup), slide presentations, PiP. Defines 17 action types (play, pause, stop, seek*, previous/nexttrack, skipad, togglemicrophone/camera/screenshare, hangup, previous/nextslide, enterpictureinpicture, voiceactivity). ~94% global usage; interop on newer state methods uneven.
- **Direction / roadmap:** Growth on the action/metadata surface: `enterfullscreen` (#372), `record` (#365), reactions/thumbs (#366), playback-rate handler (#361), site-provided transcripts (#370), lock-screen action hints (#374). Conferencing state methods + `setPositionState` are recently landed, still stabilizing.
- **Hot discussions (top 3-5):**
  - [#374](https://github.com/w3c/mediasession/issues/374) — page hints for which actions appear on compact/lock-screen surfaces (limited UA slots).
  - [#372](https://github.com/w3c/mediasession/issues/372) — add `enterfullscreen`; ties to #358 (user-triggered vs auto fullscreen, a gesture/security concern).
  - [#370](https://github.com/w3c/mediasession/issues/370) — site-provided transcripts (a11y + assistant).
  - [#368](https://github.com/w3c/mediasession/issues/368) — expand beyond OS-provided surfaces.
  - [#361](https://github.com/w3c/mediasession/issues/361) — dedicated playbackrate action handler. Plus a11y: #356/#357 (Accessibility Considerations + self-review).
- **Pushback / risks / problems:** Interop drift across the growing action set — engines implement different subsets, so advertised "supported actions" vary → inconsistent controls. Conferencing state methods the biggest gap (**Firefox implements none**). `setScreenshareActive` is **Safari-only** (single-engine). New actions raise gesture/permission + UI-real-estate questions. Nothing formally marked at-risk.
- **WPT status:** 9 test files / ~130 subtests (2026-07-12/13). Chrome 120/130 (~92%), Safari 105/130 (~81%), **Firefox 89/130 (~68%)** — clear laggard; gaps in conferencing state methods + newer actions.
- **Browser support:** Core (`setActionHandler`, `metadata`, `playbackState`) everywhere — Chrome 73+, Firefox 82+, Safari 15+. `setPositionState`: universal. Conferencing methods diverge: `setCameraActive`/`setMicrophoneActive` — Chrome 93, Safari 18.4, **Firefox none**; `setScreenshareActive` — **Safari 18.4 only**.
- **Co-chair attention flags:** Firefox's low WPT + absent mic/camera/screenshare methods — the biggest interop hole; status check with Mozilla. `setScreenshareActive` single-engine — track whether Chromium commits. Wave of new-action proposals (#372/#365/#366/#361) + lock-screen hinting (#374) needs a coherent extensibility/prioritization story before more land ad hoc. A11y deliverables (#356/#357) + transcripts (#370) may need nudging before CR. `enterfullscreen` + gesture semantics (#358/#372) to watch.

## Media Source Extensions (`media-source`)
- **Stage / repo / TR:** W3C **Working Draft** (latest 4 Nov 2025), targeting a v2 REC; **v1 is a REC (17 Nov 2016)**. Not yet stable ("incompatible changes possible before CR"). · w3c/media-source · [TR: media-source-2](https://www.w3.org/TR/media-source-2/).
- **One-liner:** Lets JS feed media bytes into `<audio>`/`<video>` via a `MediaSource`/`SourceBuffer` buffer model — the foundation for adaptive streaming (HLS/DASH), ad insertion, time-shifting.
- **Brief:** MSE extends `HTMLMediaElement` so pages build media streams client-side, appending segments to per-track `SourceBuffer`s and adapting to network/CPU. Format-agnostic. v2 adds: `changeType()` codec/container switching, MSE in dedicated workers, and `ManagedMediaSource`/`ManagedSourceBuffer`/`BufferedChangeEvent` for UA-managed, power-efficient buffering. `URL.createObjectURL(MediaSource)` removed (folded into File API).
- **Direction / roadmap:** (1) **MSE-in-Workers** (Chrome-led, [#175](https://github.com/w3c/media-source/issues/175)); (2) **Managed Media Source (MMS)** (Apple-led, [#320](https://github.com/w3c/media-source/issues/320)) — UA evicts buffered content + signals via `bufferedchange`; iPhone gated full MSE behind MMS; (3) codec switching via `changeType()`; (4) MSE in SharedWorker ([#371](https://github.com/w3c/media-source/issues/371), Jan 2026).
- **Hot discussions (top 3-5):**
  - Coded-frame-processing edge cases (very active 2026): PTS collisions ([#375](https://github.com/w3c/media-source/issues/375)), SAP Type 2 decode-shadowed orphans ([#374](https://github.com/w3c/media-source/issues/374)).
  - Interop when an append overlaps `currentTime` ([#373](https://github.com/w3c/media-source/issues/373)) — cross-browser divergence.
  - Modeling `seekable` for finite-duration MediaSource ([#369](https://github.com/w3c/media-source/issues/369)).
  - Worker scoping: `TrackList` in a DedicatedWorker ([#361](https://github.com/w3c/media-source/issues/361)); SharedWorker ([#371](https://github.com/w3c/media-source/issues/371)).
- **Pushback / risks / problems:** ~112 open issues. Real interop divergence in coded-frame processing / overlapping appends (the 2026 cluster) — historically under-specified, browser-specific. **MMS is effectively single-vendor** (Safari-only). **Worker support badly split.** UA-controlled eviction is hard to test/reason about.
- **WPT status:** ~82 test files. Aligned experimental (13 Jul 2026): Chrome 84.9% (550/648), Safari 88.4% (558/631), Firefox 78.5% (466/594). **Worker tests expose the split:** Chrome 70/70 (100%), Safari 39/73 (~53%), **Firefox 3/62 (~5%, unimplemented)**. **Gap: no dedicated ManagedMediaSource/eviction coverage found** despite Safari shipping it.
- **Browser support:** MSE v1 universal (Chrome 23+, Firefox 42+, Safari 8+, Edge 12+). **Managed Media Source Safari-first/only** (macOS Safari 17.0+, iOS 17.1+; Chrome/Edge/Firefox unsupported per caniuse — treat Chrome MMS as uncertain). **MSE-in-Workers Chrome-first** (~108); Safari partial; **Firefox not shipped** (~5% worker WPT). Safari MMS quirk: `sourceopen` only fires with `disableRemotePlayback=true` or an AirPlay `<source>` alternative.
- **Co-chair attention flags:** Foundational, high-stakes streaming spec (YouTube/Netflix/etc.) — but v2 advances two **vendor-specific extensions on opposite sides**: Apple's MMS (Safari-only) and Google's MSE-in-Workers (Firefox missing). Watch: (a) single-vendor lock-in on MMS + whether others commit before CR, (b) Firefox's worker gap, (c) 2026 coded-frame-processing interop bugs (core append model still not fully interoperable), (d) thin/absent MMS WPT. Good candidate for an Interop focus area + multi-implementer commitment before v2 CR/REC.

## Picture-in-Picture (`picture-in-picture`)
- **Stage / repo / TR:** W3C Working Draft (16 June 2026), Rec track, pushing toward CR · [w3c/picture-in-picture](https://github.com/w3c/picture-in-picture) · [TR](https://www.w3.org/TR/picture-in-picture/).
- **One-liner:** Lets a site float an `HTMLVideoElement` in an always-on-top OS-level window.
- **Brief:** `HTMLVideoElement.requestPictureInPicture()` / `Document.exitPictureInPicture()`, `disablePictureInPicture`, `Document.pictureInPictureEnabled`, `pictureInPictureElement`, a `PictureInPictureWindow` interface (`width`/`height`/`onresize`), and `enter`/`leavepictureinpicture` events. Video-only by design. Widely shipped; current work is algorithm cleanup + edge-case hardening.
- **Direction / roadmap:** Maturing toward CR (recent issues are spec-plumbing: fully-active-document checks, detached frames, exit-algorithm refactor). Big adjacent question: **[Document Picture-in-Picture](https://wicg.github.io/document-picture-in-picture/)** (a full `Document`, not just video) is incubated in **WICG, not this spec / not MediaWG** — the natural migration candidate, but that transfer hasn't formally happened; confirm against the charter. Already shipping (Firefox 151 shipped Document PiP, [Phoronix](https://www.phoronix.com/news/Firefox-151)).
- **Hot discussions (top 3-5):**
  - [#261](https://github.com/w3c/picture-in-picture/issues/261) — **"Transient user activation to not consume?" (CR Blocking):** real break (Whereby calling `requestPictureInPicture()` + `getDisplayMedia()` from one gesture); proposal to *check* activation without consuming it.
  - [#262](https://github.com/w3c/picture-in-picture/issues/262) — require a fully active document.
  - [#263](https://github.com/w3c/picture-in-picture/issues/263) — remove global "initiators of active PiP sessions" state.
  - Recurring across ~23 open issues: multiple simultaneous PiP windows, detached elements, throw-vs-reject clarity.
- **Pushback / risks / problems:** Safari historically ships its own `webkitSupportsPresentationMode`/`webkitSetPresentationMode` rather than the standard surface, so cross-browser code branches; caniuse shows long "partial support" tails. #261 activation-consumption is a live interop/usability risk and CR-blocking. `mediastream` + shadow-DOM edge cases diverge.
- **WPT status:** ~16 test files (enter/exit/leave, disable attr, element/window interfaces, mediastream, shadow-dom, permissions-policy, etc.). Exact per-browser pass rates **not** retrievable programmatically — read wpt.fyi live. Expectation: high Chrome/Edge, Safari most likely to show gaps.
- **Browser support:** ~92%+ global. Chrome 70+/Edge 79+ full. Safari 13.1+ full (historically via WebKit presentation-mode API; iOS 14+). **Firefox: standard `requestPictureInPicture()` shipped in Firefox 153** (bug 1463402) — before that only Firefox's own toolkit PiP UI, not the web API. Android/Chrome-for-Android partial.
- **Co-chair attention flags:** **Scope/governance:** clarify whether Document PiP is (or should be) coming onto the MediaWG track vs staying in WICG — the biggest strategic question, and it's already shipping ahead of any W3C-track status. **CR-blocker #261** — resolve before CR (concrete web-compat impact). **Safari interop** — legacy `webkitPresentationMode` vs standard; watch the WPT Safari column. Confirm live WPT numbers.

## WebCodecs (`webcodecs`)
- **Stage / repo / TR:** W3C Working Draft (Rec track), latest 8 July 2026; moving toward CR (scope being finalized) · [w3c/webcodecs](https://github.com/w3c/webcodecs) · [TR](https://www.w3.org/TR/webcodecs/).
- **One-liner:** Low-level JS access to the browser's built-in audio, video, and image encoders/decoders, decoupled from any container or transport.
- **Brief:** `VideoEncoder`/`VideoDecoder`, `AudioEncoder`/`AudioDecoder`, raw types `VideoFrame`/`AudioData`, encoded types `EncodedVideoChunk`/`EncodedAudioChunk`, and `ImageDecoder`. Implementers may support any/no codecs. Codec-specific config lives in the companion [WebCodecs Codec Registry](https://www.w3.org/TR/webcodecs-codec-registry/) (Registry Draft, 12 Feb 2026). Interoperates with Streams, WebGPU/WebGL, WASM, WebTransport, WebRTC.
- **Direction / roadmap:** Editors want to lock a stable baseline and advance to CR ([#783](https://github.com/w3c/webcodecs/issues/783), "define scope for CR"); charter targeted CR ~2026 but July 2026 is still WD (slipped). Ongoing: codec-registry growth, color-space/HDR, richer image decoding, encoder stats (PSNR), RTC controls (reference-frame control).
- **Hot discussions (top 3-5):**
  - [#41](https://github.com/w3c/webcodecs/issues/41) / [#483](https://github.com/w3c/webcodecs/issues/483) — content protection / EME integration for a container-less API; long-running.
  - [#626](https://github.com/w3c/webcodecs/issues/626) — audio priming/padding samples without container info; **CR-blocking**.
  - [#285](https://github.com/w3c/webcodecs/issues/285) — reference-frame control (RTC, TPAC2024).
  - [#940](https://github.com/w3c/webcodecs/issues/940) — ColorSpace override underspecified (Media WG agenda, Jul 2026); [#166](https://github.com/w3c/webcodecs/issues/166) — diagrams/definitions for VideoFrame concepts.
  - Image-decoding cluster: #205 (decouple decode/demux), #932/#934 (ImageTrack repetition, unhandled `completed`).
- **Pushback / risks / problems:** No content-protection/EME story yet → blocks premium-media adoption of the low-level path. Fingerprinting via codec/capability enumeration. Codec licensing shapes what UAs ship (AAC encode unsupported in Firefox + desktop Linux; HEVC varies). At-risk/underspecified: audio priming, color space, out-of-order (IPPP) decoding. Recent Chrome WebCodecs memory-disclosure CVE (CVE-2026-5888). **Not an Interop 2026 focus area** → cross-browser convergence isn't pushed there.
- **WPT status:** Tests under `/webcodecs/` (audio/video encode+decode, VideoFrame, AudioData, ImageDecoder, config). Exact counts not reliably scrapable. Qualitatively: Chrome passes the vast majority; Firefox passes most video/decoder tests (audio-encode gaps, esp. AAC); Safari's pass rate rose sharply with Safari 26. Treat percentages as unverified.
- **Browser support:** Chrome/Edge 94+ (led design, most complete). Firefox 130+ desktop (full audio+video); Android lacks it; AAC encode unsupported on any Firefox/Linux. Safari 16.4–18.7 video-only partial; **Safari 26.0** added full support (audio/video/image) across macOS/iOS/iPadOS.
- **Co-chair attention flags:** One of the highest-activity, widest-surface specs with heavy cross-WG deps (EME, WebGPU/WebGL, Streams, WebRTC, WASM, WebTransport). Watch the **path to CR** ([#783](https://github.com/w3c/webcodecs/issues/783)) and clearing CR-blockers (audio priming [#626](https://github.com/w3c/webcodecs/issues/626), color-space [#940](https://github.com/w3c/webcodecs/issues/940)); track the parallel Codec Registry as its own maturity stream; monitor the EME/content-protection gap + security/fingerprinting posture given the attack surface.

---

## Cross-spec patterns for priority-setting

- **Single-vendor specs blocking their own CR:** Autoplay (Firefox-only), Audio Session (Safari-only). Neither can honestly meet a "2 interoperable implementations" CR-exit bar today. Chair action: get explicit multi-vendor commitment or reset the charter expectation.
- **Vendor-split within one spec:** MSE (Apple MMS vs Google Workers), Media Session (conferencing methods Chrome/Safari, Firefox absent). Chair action: push for the *other* engines to commit before advancing the split features; consider marking them at-risk.
- **Privacy/fingerprinting is the common horizontal blocker:** Media Capabilities (#209), Autoplay (#42/#43), WebCodecs (capability enumeration), EME (identifiers). Get PING engaged early on all four.
- **Interop focus-area leverage:** MSE and Media Capabilities are strong candidates to nominate for a future Interop cycle to force cross-vendor convergence and WPT investment. WebCodecs is notably absent from Interop 2026 despite its importance.
- **WPT is the universal gate:** every spec's CR→PR path runs through WPT all-engines pass rates. Audio Session, Media Playback Quality, and the MMS parts of MSE have the thinnest coverage — test investment must precede any CR push there.
</content>
