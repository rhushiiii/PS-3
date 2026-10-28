export function Icon({
  name,
}: {
  name:
    | "building"
    | "arrow"
    | "grid"
    | "menu"
    | "close"
    | "exit"
    | "history"
    | "upload";
}) {
  const paths = {
    building:
      "M4 21V7l8-4 8 4v14M8 9h1m6 0h1M8 13h1m6 0h1M10 21v-4h4v4M2 21h20",
    arrow: "M5 12h14m-5-5 5 5-5 5",
    grid: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z",
    menu: "M4 6h16M4 12h16M4 18h16",
    close: "m6 6 12 12M18 6 6 18",
    exit: "M10 4H4v16h6m4-12 4 4-4 4m-6-4h10",
    history: "M4 4v5h5M4.6 9a8 8 0 1 1-.4 7M12 7v5l3 2",
    upload: "M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6",
  };
  return (
    <svg
      aria-hidden="true"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d={paths[name]} />
    </svg>
  );
}
