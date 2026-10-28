export function BrandMark({ tagline }: { tagline?: string }) {
  return (
    <span className="brand">
      <span className="brand-mark" aria-hidden="true">
        P
      </span>
      <span className="brand-name">
        PRAVYA
        {tagline && <small>{tagline}</small>}
      </span>
    </span>
  );
}
