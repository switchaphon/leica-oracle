// A prediction ledger that cannot be edited after the fact.
//
// WHY THIS EXISTS
//
// On 2026-08-07 I published a reading for Friday the 7th: Moon in ภพ ๒ กดุมภะ under
// โจโรฤกษ์, therefore a day to watch assets and money. That Friday, a 14-year-old
// killed his grandparents and then eight or nine people at a school in Nonthaburi.
//
// My reading missed. And within seconds of reading the news I could see three clean
// ways to make it look like a hit: โจโร translates as *thief*, so read it as violence;
// transiting Venus sat in the city chart's ภพ ๘ มรณะ; Ketu was parked in the 7th.
// Any of them, written up confidently, would have read as uncanny.
//
// All three occurred to me AFTER the outcome. That is the whole problem. An
// astrologer with a good memory and a flexible vocabulary is never wrong, and a
// system that is never wrong has told you nothing.
//
// I declined to retrofit, and declining worked — but it worked because I happened to
// be paying attention, and that is not a safeguard. So the rule moves out of my
// judgement and into the type system: a Prediction is frozen with a timestamp and a
// digest, an Outcome carries its own, and score() REFUSES any mechanism whose
// committedAt is later than the outcome. Not "discourages". Refuses.
//
// The five failure modes below all came from real misses in this project, mine and
// other engines'. Each one is now a machine check instead of a thing to remember.

import { createHash } from "node:crypto";

/** How wide a question is. A mechanism must not outlive it. */
export type Horizon = "day" | "fortnight" | "month" | "year";

export const HORIZON_DAYS: Record<Horizon, number> = {
  day: 1, fortnight: 14, month: 30, year: 365,
};

/**
 * The kind of thing predicted. Naming the domain is what separates "I said something
 * bad would happen" from a claim that can miss — and on 2026-08-07 it is exactly what
 * I got wrong: I named assets, the day delivered mass killing.
 */
export type Domain =
  | "money" | "work" | "study" | "residence" | "relationship"
  | "health" | "travel" | "conflict" | "death" | "reputation";

export type Mechanism = {
  description: string;
  /** Years the configuration holds. Compared against the question's horizon. */
  lifetimeDays: number;
  /** Fraction of comparable windows in which this signal fires anyway. */
  baseRate: number;
  /** Set once, at commit time. Anything added later is a retrofit. */
  committedAt: string; // ISO 8601
};

export type Prediction = {
  claim: string;
  domain: Domain;
  horizon: Horizon;
  /** The window the claim is about. */
  windowStart: string;
  windowEnd: string;
  confidence: number;      // 0..1
  noChartPrior: number;    // 0..1 — what an informed guess without the chart gives
  mechanisms: Mechanism[];
  committedAt: string;
};

export type Outcome = {
  happened: boolean;
  /** What kind of event actually occurred. Compared against the predicted domain. */
  domain: Domain | null;
  note: string;
  observedAt: string;
};

export type Verdict = "hit" | "miss" | "unscorable";

export type Score = {
  verdict: Verdict;
  mechanismVerdict: Verdict;
  chartContribution: number;
  /** Every reason the score is what it is, in the order they were checked. */
  reasons: string[];
  /** Mechanisms rejected for being added after the outcome was known. */
  retrofitted: Mechanism[];
};

/** Stable digest of a prediction, so a commit can be proved to predate an outcome. */
export function digest(p: Prediction): string {
  const canonical = JSON.stringify({
    claim: p.claim, domain: p.domain, horizon: p.horizon,
    windowStart: p.windowStart, windowEnd: p.windowEnd,
    confidence: p.confidence, noChartPrior: p.noChartPrior,
    mechanisms: p.mechanisms.map((m) => [m.description, m.lifetimeDays, m.baseRate, m.committedAt]),
    committedAt: p.committedAt,
  });
  return createHash("sha256").update(canonical).digest("hex").slice(0, 16);
}

/** Base rate above which a signal fires too often to explain anything. */
export const BASE_RATE_CEILING = 0.35;

/**
 * Score a prediction against what happened.
 *
 * The order matters: structural disqualifications are checked BEFORE the verdict, so
 * a mechanism that could never have selected this window is never credited with
 * having done so — even when the claim turns out true.
 */
export function score(p: Prediction, o: Outcome): Score {
  const reasons: string[] = [];

  // 1. Retrofit check first. A mechanism minted after the outcome is not evidence,
  //    it is a memory of the outcome wearing a mechanism's clothes.
  const retrofitted = p.mechanisms.filter((m) => m.committedAt > o.observedAt);
  const honest = p.mechanisms.filter((m) => m.committedAt <= o.observedAt);
  for (const m of retrofitted) {
    reasons.push(`retrofit rejected: "${m.description}" was committed after the outcome was known`);
  }

  // 2. Timescale. A condition true for a year cannot pick a day out of that year.
  const windowDays = HORIZON_DAYS[p.horizon];
  const tooSlow = honest.filter((m) => m.lifetimeDays > windowDays * 3);
  for (const m of tooSlow) {
    reasons.push(`climate not cause: "${m.description}" holds ${m.lifetimeDays}d for a ${windowDays}d question`);
  }

  // 3. Base rate. A signal that fires half the time explains nothing it is credited with.
  const tooCommon = honest.filter((m) => m.baseRate > BASE_RATE_CEILING);
  for (const m of tooCommon) {
    reasons.push(`not discriminating: "${m.description}" fires in ${(m.baseRate * 100).toFixed(0)}% of comparable windows`);
  }

  const surviving = honest.filter(
    (m) => m.lifetimeDays <= windowDays * 3 && m.baseRate <= BASE_RATE_CEILING
  );

  // 4. Verdict on the claim itself — and the domain must match. "Something bad
  //    happened" is not a hit for a prediction about money.
  let verdict: Verdict;
  if (!o.happened) {
    verdict = "miss";
    reasons.push("claimed event did not occur");
  } else if (o.domain !== p.domain) {
    verdict = "miss";
    reasons.push(`domain mismatch: predicted ${p.domain}, observed ${o.domain}`);
  } else {
    verdict = "hit";
    reasons.push(`domain matched: ${p.domain}`);
  }

  // 5. The mechanism is scored separately, because being right for a bad reason is
  //    luck, and a ledger with one column records luck as skill and reuses the reason.
  let mechanismVerdict: Verdict;
  if (surviving.length === 0) {
    mechanismVerdict = "unscorable";
    reasons.push("no mechanism survived the structural checks — nothing to credit or blame");
  } else if (verdict === "hit") {
    mechanismVerdict = "hit";
  } else {
    mechanismVerdict = "miss";
  }

  return {
    verdict,
    mechanismVerdict,
    chartContribution: +(p.confidence - p.noChartPrior).toFixed(3),
    reasons,
    retrofitted,
  };
}

/** One-line summary for a report. Deliberately blunt. */
export function summarise(s: Score): string {
  return `verdict=${s.verdict} · mechanism=${s.mechanismVerdict} · ` +
    `chart_contribution=${s.chartContribution >= 0 ? "+" : ""}${s.chartContribution}` +
    (s.retrofitted.length ? ` · ${s.retrofitted.length} retrofit(s) rejected` : "");
}
