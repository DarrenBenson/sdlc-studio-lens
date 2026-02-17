/**
 * SearchBar component tests.
 * Test cases: TC0239-TC0244 from TS0023.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { describe, expect, it } from "vitest";

import { SearchBar } from "../../src/components/SearchBar";

/** Helper that renders the current pathname + search string. */
function LocationDisplay() {
  const location = useLocation();
  return (
    <div data-testid="location">
      {location.pathname}
      {location.search}
    </div>
  );
}

function renderSearchBar(initialPath = "/") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route
          path="*"
          element={
            <>
              <SearchBar />
              <LocationDisplay />
            </>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

// ---------------------------------------------------------------------------
// TC0239: Search bar renders with placeholder
// ---------------------------------------------------------------------------

describe("TC0239: Search bar renders with placeholder", () => {
  it("displays input with correct placeholder text", () => {
    renderSearchBar();
    const input = screen.getByPlaceholderText("Search documents...");
    expect(input).toBeInTheDocument();
    expect(input).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// TC0240: Enter submits and navigates
// ---------------------------------------------------------------------------

describe("TC0240: Enter submits and navigates", () => {
  it("navigates to /search?q=authentication on Enter", async () => {
    const user = userEvent.setup();
    renderSearchBar();

    const input = screen.getByPlaceholderText("Search documents...");
    await user.type(input, "authentication");
    await user.keyboard("{Enter}");

    expect(screen.getByTestId("location")).toHaveTextContent(
      "/search?q=authentication",
    );
  });
});

// ---------------------------------------------------------------------------
// TC0241: Query preserved from URL
// ---------------------------------------------------------------------------

describe("TC0241: Query preserved from URL", () => {
  it("populates input value from URL search params", () => {
    renderSearchBar("/search?q=authentication");

    const input = screen.getByPlaceholderText("Search documents...");
    expect(input).toHaveValue("authentication");
  });
});

// ---------------------------------------------------------------------------
// TC0242: Slash key focuses search bar
// ---------------------------------------------------------------------------

describe("TC0242: Slash key focuses search bar", () => {
  it("focuses input when / is pressed with no active input", async () => {
    const user = userEvent.setup();
    renderSearchBar();

    const input = screen.getByPlaceholderText("Search documents...");
    // Ensure input is not focused initially
    expect(input).not.toHaveFocus();

    // Press slash key on the document body
    await user.keyboard("/");

    expect(input).toHaveFocus();
  });
});

// ---------------------------------------------------------------------------
// TC0243: Empty submit does not navigate
// ---------------------------------------------------------------------------

describe("TC0243: Empty submit does not navigate", () => {
  it("stays on current URL when submitting empty input", async () => {
    const user = userEvent.setup();
    renderSearchBar("/");

    const input = screen.getByPlaceholderText("Search documents...");
    await user.click(input);
    await user.keyboard("{Enter}");

    expect(screen.getByTestId("location")).toHaveTextContent("/");
  });
});

// ---------------------------------------------------------------------------
// TC0244: Whitespace-only submit prevented
// ---------------------------------------------------------------------------

describe("TC0244: Whitespace-only submit prevented", () => {
  it("does not navigate when input contains only spaces", async () => {
    const user = userEvent.setup();
    renderSearchBar("/");

    const input = screen.getByPlaceholderText("Search documents...");
    await user.type(input, "   ");
    await user.keyboard("{Enter}");

    expect(screen.getByTestId("location")).toHaveTextContent("/");
  });
});
