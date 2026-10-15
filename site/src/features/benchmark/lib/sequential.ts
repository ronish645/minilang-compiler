// Sequential (magnitude) encoding for rates: one blue hue, light -> dark in
// light mode; the tokens flip the anchor in dark mode, so text color is chosen
// per step and per theme to keep contrast.

export const SEQ_STEPS = [
  { token: "var(--seq-100)", min: 0, label: "0–19%" },
  { token: "var(--seq-250)", min: 0.2, label: "20–39%" },
  { token: "var(--seq-400)", min: 0.4, label: "40–59%" },
  { token: "var(--seq-550)", min: 0.6, label: "60–79%" },
  { token: "var(--seq-700)", min: 0.8, label: "80–100%" },
] as const;

// Light ramp: 100/250/400 are light enough for dark ink; 550/700 need light text.
// Dark ramp: 100/250 are dark (light ink works); 400+ are light (need dark text).
// --page is near-white in light mode and near-black in dark mode, so it serves
// as the "inverse" text color.
const TEXT_CLASS = [
  "text-ink",
  "text-ink",
  "text-ink dark:text-page",
  "text-page",
  "text-page",
] as const;

export const seqIndex = (value: number) => {
  let index = 0;
  SEQ_STEPS.forEach((step, i) => {
    if (value >= step.min) index = i;
  });
  return index;
};

export const seqFill = (value: number) => SEQ_STEPS[seqIndex(value)].token;
export const seqTextClass = (value: number) => TEXT_CLASS[seqIndex(value)];
