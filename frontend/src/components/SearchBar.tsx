import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";

/** Global search bar with keyboard shortcut support. */
export function SearchBar(): React.JSX.Element {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialise from URL query parameter
  const [query, setQuery] = useState(searchParams.get("q") ?? "");

  // Keep input in sync when URL changes externally
  useEffect(() => {
    setQuery(searchParams.get("q") ?? "");
  }, [searchParams]);

  // Handle Enter key submission
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "Enter") {
      const trimmed = query.trim();
      if (trimmed.length > 0) {
        navigate(`/search?q=${encodeURIComponent(trimmed)}`);
      }
    }
  };

  // Register `/` keyboard shortcut to focus the search bar
  useEffect(() => {
    const handleSlash = (e: KeyboardEvent): void => {
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") {
        return;
      }
      if (e.key === "/") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };

    document.addEventListener("keydown", handleSlash);
    return () => {
      document.removeEventListener("keydown", handleSlash);
    };
  }, []);

  return (
    <div className="relative flex w-full max-w-md items-center">
      {/* Magnifying glass icon */}
      <svg
        className="pointer-events-none absolute left-3 h-4 w-4 text-text-tertiary"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={2}
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
        />
      </svg>

      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Search documents..."
        className="w-full rounded-lg border border-border-default bg-bg-base py-1.5 pl-9 pr-3 text-sm text-text-primary placeholder:text-text-tertiary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
      />
    </div>
  );
}
