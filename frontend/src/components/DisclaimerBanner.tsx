export function DisclaimerBanner({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <p className="text-[11px] leading-relaxed text-ink-muted">
        Informational only — not investment advice. Data may be delayed. Past performance ≠ future
        results.
      </p>
    );
  }
  return (
    <div className="border-t border-ink/10 bg-ink/[0.03] px-5 py-4 text-center text-[11px] leading-relaxed text-ink-muted md:px-8">
      Atlas is for informational and educational purposes only. Nothing on this site is investment,
      tax, or legal advice. Market data may be delayed. Past performance does not guarantee future
      results. You are solely responsible for your trading decisions.
    </div>
  );
}
